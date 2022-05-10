from decimal import Decimal

from brownie import interface

from great_ape_safe import GreatApeSafe
from helpers.addresses import registry


# only set to true when actually ready to post and exec on mainnet
COW_PROD = False

SAFE = GreatApeSafe(registry.eth.badger_wallets.techops_multisig)
SAFE.init_badger()
SAFE.init_cow(prod=COW_PROD)
PROCESSOR = SAFE.badger.bribes_processor

WETH = interface.IWETH9(registry.eth.treasury_tokens.WETH, owner=SAFE.account)
BADGER = interface.ERC20(
    registry.eth.treasury_tokens.BADGER, owner=SAFE.account
)
CVX = interface.ERC20(registry.eth.treasury_tokens.CVX, owner=SAFE.account)

# percentage of the bribes that is used to buyback $badger
BADGER_SHARE = .275
# percentage of the bribes that are dedicated to the treasury
OPS_FEE = .05


def step0_1(sim=False):
    bribes_dest = GreatApeSafe(PROCESSOR.address)
    bribes_dest.take_snapshot(registry.eth.bribe_tokens_claimable.values())

    if sim:
        from brownie_tokens import MintableForkToken
        alcx = MintableForkToken(registry.eth.treasury_tokens.ALCX)
        alcx._mint_for_testing(SAFE.badger.strat_bvecvx, 500e18)
        claimed = {alcx.address: 500e18}
    else:
        claimed = SAFE.badger.claim_bribes_votium(
            registry.eth.bribe_tokens_claimable
        )
    for addr, mantissa in claimed.items():
        order_payload, order_uid = SAFE.badger.get_order_for_processor(
            sell_token=SAFE.contract(addr),
            mantissa_sell=mantissa,
            buy_token=WETH,
            coef=.99,
            prod=COW_PROD
        )
        PROCESSOR.sellBribeForWeth(order_payload, order_uid)
        SAFE.badger.claim_bribes_convex(registry.eth.bribe_tokens_claimable)

    bribes_dest.print_snapshot()

    SAFE.post_safe_tx(call_trace=True)


def step0(sim=False):
    '''can be skipped if step0_1 was successful'''

    bribes_dest = GreatApeSafe(PROCESSOR.address)
    bribes_dest.take_snapshot(registry.eth.bribe_tokens_claimable.values())

    if sim:
        from brownie_tokens import MintableForkToken
        alcx = MintableForkToken(registry.eth.treasury_tokens.ALCX)
        alcx._mint_for_testing(SAFE.badger.strat_bvecvx, 500e18)
    else:
        SAFE.badger.claim_bribes_votium(registry.eth.bribe_tokens_claimable)
        SAFE.badger.claim_bribes_convex(registry.eth.bribe_tokens_claimable)

    bribes_dest.print_snapshot()

    SAFE.post_safe_tx(call_trace=True)


def step1():
    '''can be skipped if step0_1 was successful'''

    want_to_sell = registry.eth.bribe_tokens_claimable.copy()
    want_to_sell.pop('CVX') # SameBuyAndSellToken
    want_to_sell.pop('MTA') # dust
    want_to_sell.pop('NSBT') # dust
    for _, addr in want_to_sell.items():
        token = SAFE.contract(addr)
        balance = token.balanceOf(SAFE.badger.strat_bvecvx)
        if balance == 0:
            continue
        order_payload, order_uid = SAFE.badger.get_order_for_processor(
            sell_token=token,
            mantissa_sell=balance,
            buy_token=WETH,
            coef=.99,
            prod=COW_PROD
        )
        PROCESSOR.sellBribeForWeth(order_payload, order_uid)
    SAFE.post_safe_tx(call_trace=True)


def step2():
    badger_share = WETH.balanceOf(PROCESSOR) * BADGER_SHARE
    cvx_share = WETH.balanceOf(PROCESSOR) - badger_share
    assert badger_share + cvx_share == WETH.balanceOf(PROCESSOR)

    order_payload, order_uid = SAFE.badger.get_order_for_processor(
        sell_token=WETH,
        mantissa_sell=badger_share,
        buy_token=BADGER,
        coef=.99,
        prod=COW_PROD
    )
    # bribes processor doesnt accept fee > 10% of total order
    assert int(order_payload[7]) < .1 * int(order_payload[3])
    PROCESSOR.swapWethForBadger(order_payload, order_uid)

    order_payload, order_uid = SAFE.badger.get_order_for_processor(
        sell_token=WETH,
        mantissa_sell=cvx_share,
        buy_token=CVX,
        coef=.99,
        prod=COW_PROD
    )
    # bribes processor doesnt accept fee > 10% of total order
    assert int(order_payload[7]) < .1 * int(order_payload[3])
    PROCESSOR.swapWethForCVX(order_payload, order_uid)

    SAFE.post_safe_tx(call_trace=True)


def step2_redo_cvx(badger_share):
    badger_share = Decimal(badger_share)
    cvx_share = WETH.balanceOf(PROCESSOR) - badger_share

    order_payload, order_uid = SAFE.badger.get_order_for_processor(
        sell_token=WETH,
        mantissa_sell=cvx_share,
        buy_token=CVX,
        coef=.99,
        prod=COW_PROD
    )
    # bribes processor doesnt accept fee > 10% of total order
    assert int(order_payload[7]) < .1 * int(order_payload[3])
    PROCESSOR.swapWethForCVX(order_payload, order_uid)

    SAFE.post_safe_tx(call_trace=True)


def step3():
    if CVX.balanceOf(PROCESSOR) > 0:
        PROCESSOR.swapCVXTobveCVXAndEmit()
    if BADGER.balanceOf(PROCESSOR) > 0:
        PROCESSOR.emitBadger()
    SAFE.post_safe_tx(call_trace=True)
