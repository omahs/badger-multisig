from this import d
from brownie import Contract, chain

from great_ape_safe import GreatApeSafe
from helpers.addresses import r


LEVERAGE_RATE = 1.5

SAFE = GreatApeSafe(r.badger_wallets.treasury_ops_multisig)
WBTC = SAFE.contract(r.treasury_tokens.WBTC)
USDC = SAFE.contract(r.treasury_tokens.USDC)
CWBTC = SAFE.contract(r.treasury_tokens.cWBTC)
CUSDC = SAFE.contract(r.treasury_tokens.cUSDC)

SAFE.init_chainlink()
BTC_RATE = Contract(r.chainlink.feed_registry).latestRoundData(
    SAFE.chainlink.BTC_HEX, SAFE.chainlink.USD_HEX
)[1] / 1e8


def get_btc_balances():
    bal_wbtc = WBTC.balanceOf(SAFE)
    bal_usdc = USDC.balanceOf(SAFE)
    bal_cwbtc = CWBTC.balanceOf(SAFE)

    btc_bal_wbtc = bal_wbtc
    btc_bal_usdc = bal_usdc / BTC_RATE * 1e2
    btc_bal_cwbtc = bal_cwbtc * CWBTC.exchangeRateStored() / 1e18
    return btc_bal_wbtc, btc_bal_usdc, btc_bal_cwbtc


def get_leverage_ratio():
    btc_bal_wbtc, btc_bal_usdc, btc_bal_cwbtc = get_btc_balances()
    try:
        return (btc_bal_wbtc + btc_bal_cwbtc) / btc_bal_cwbtc
    except ZeroDivisionError:
        return 1.


def set_leverage_ratio(target_lr=LEVERAGE_RATE):
    SAFE.take_snapshot([WBTC, USDC, CWBTC])


    current_lr = get_leverage_ratio()
    print(current_lr)

    delta = float(target_lr) - current_lr

    btc_bal_wbtc, btc_bal_usdc, btc_bal_cwbtc = get_btc_balances()

    usdc_to_borrow = (btc_bal_wbtc + btc_bal_cwbtc) * BTC_RATE * (delta) / 1e2
    print('to borrow:', usdc_to_borrow)

    if usdc_to_borrow > 0:
        SAFE.init_compound()
        SAFE.compound.deposit(WBTC, WBTC.balanceOf(SAFE))
        SAFE.compound.borrow(WBTC, USDC, usdc_to_borrow)

        SAFE.init_uni_v2()  # TODO: implement swap functions for uni v3
        SAFE.uni_v2.swap_tokens_for_tokens(USDC, usdc_to_borrow, [USDC, WBTC])

    # SAFE.init_uni_v3()
    # USDC.approve(SAFE.uni_v3.router, usdc_to_borrow)
    # SAFE.uni_v3.router.exactInputSingle(
    #     [
    #         USDC.address,  # address tokenIn;
    #         WBTC.address,  # address tokenOut;
    #         3000,  # uint24 fee;
    #         SAFE.address,  # address recipient;
    #         chain.time() + 60 * 180,  # uint256 deadline;
    #         usdc_to_borrow,  # uint256 amountIn;
    #         0,  # uint256 amountOutMinimum;
    #         0,  # uint160 sqrtPriceLimitX96;
    #     ]
    # )

    SAFE.print_snapshot()

    print(get_leverage_ratio())


# def deleverage():
#     SAFE.init_compound()
#     if get_leverage_ratio() > 1.5:

#     SAFE.uni_v2.swap_tokens_for_tokens(WBTC, 2e8, [WBTC, USDC])
#     SAFE.compound.repay(USDC)
#     # SAFE.uni_v2.swap_tokens_for_tokens(USDC, USDC.balanceOf(SAFE), [USDC, WBTC])

#     SAFE.print_snapshot()
#     print(get_leverage_ratio())


def main():
    set_leverage_ratio(1.1)
    set_leverage_ratio(1.2)
