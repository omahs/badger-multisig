from brownie import Contract

from great_ape_safe import GreatApeSafe
from helpers.addresses import r


WBTC_TO_DEPOSIT = 5
LEVERAGE_RATE = 1.5

SAFE = GreatApeSafe(r.badger_wallets.treasury_ops_multisig)
WBTC = SAFE.contract(r.treasury_tokens.WBTC)
USDC = SAFE.contract(r.treasury_tokens.USDC)
CWBTC = SAFE.contract(r.treasury_tokens.cWBTC)

SAFE.init_chainlink()
BTC_RATE = Contract(r.chainlink.feed_registry).latestRoundData(
    SAFE.chainlink.BTC_HEX, SAFE.chainlink.USD_HEX
)[1] / 1e8
USDC_TO_BORROW = WBTC_TO_DEPOSIT * BTC_RATE * (LEVERAGE_RATE - 1)


def main():
    SAFE.take_snapshot([WBTC, USDC, CWBTC])

    SAFE.init_compound()
    SAFE.compound.deposit(WBTC, WBTC_TO_DEPOSIT * 1e8)
    SAFE.compound.borrow(WBTC, USDC, USDC_TO_BORROW * 1e6)

    SAFE.init_uni_v2()  # TODO: implement swap functions for uni v3
    SAFE.uni_v2.swap_tokens_for_tokens(USDC, USDC_TO_BORROW * 1e6, [USDC, WBTC])

    SAFE.print_snapshot()


# def deleverage():
#     SAFE.init_compound()
    SAFE.uni_v2.swap_tokens_for_tokens(WBTC, 3e8, [WBTC, USDC])
    SAFE.compound.repay(USDC)

    SAFE.print_snapshot()
