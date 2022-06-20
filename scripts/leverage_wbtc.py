from brownie import Contract

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


def get_leverage_ratio():
    bal_wbtc = WBTC.balanceOf(SAFE)
    bal_usdc = USDC.balanceOf(SAFE)
    bal_cwbtc = CWBTC.balanceOf(SAFE)

    btc_bal_wbtc = bal_wbtc
    btc_bal_usdc = bal_usdc / BTC_RATE * 1e2
    btc_bal_cwbtc = bal_cwbtc * CWBTC.exchangeRateStored() / 1e18

    try:
        return (btc_bal_wbtc + btc_bal_cwbtc) / btc_bal_cwbtc
    except ZeroDivisionError:
        return 1.


def set_leverage_ratio(lev=LEVERAGE_RATE):
    print(get_leverage_ratio())

    SAFE.take_snapshot([WBTC, USDC, CWBTC])

    usdc_to_borrow = WBTC.balanceOf(SAFE) * BTC_RATE * (lev - 1) / 1e2

    SAFE.init_compound()
    SAFE.compound.deposit(WBTC, WBTC.balanceOf(SAFE))
    SAFE.compound.borrow(WBTC, USDC, usdc_to_borrow)

    SAFE.init_uni_v2()  # TODO: implement swap functions for uni v3
    SAFE.uni_v2.swap_tokens_for_tokens(USDC, usdc_to_borrow, [USDC, WBTC])

    SAFE.print_snapshot()

    print(get_leverage_ratio())


# def deleverage():
#     SAFE.init_compound()
    SAFE.uni_v2.swap_tokens_for_tokens(WBTC, 2e8, [WBTC, USDC])
    SAFE.compound.repay(USDC)
    # SAFE.uni_v2.swap_tokens_for_tokens(USDC, USDC.balanceOf(SAFE), [USDC, WBTC])

    SAFE.print_snapshot()
    print(get_leverage_ratio())
