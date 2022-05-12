from brownie import Contract, interface

from great_ape_safe import GreatApeSafe
from helpers.addresses import registry


DUSTY = .995


def main():
    """
    withdraw all of treasury vault's positions that hold 3pool to $usdc.
    """

    safe = GreatApeSafe(registry.eth.badger_wallets.treasury_vault_multisig)
    safe.init_curve()
    safe.init_convex()

    balance_checker = interface.IBalanceChecker(
        registry.eth.helpers.balance_checker, owner=safe.account
    )

    threepool = interface.ICurveLP(
        registry.eth.treasury_tokens.crv3pool, owner=safe.account
    )
    frax3pool = interface.IStableSwap2Pool(
        registry.eth.crv_meta_pools.crvFRAX, owner=safe.account
    )
    usdc = interface.ERC20(
        registry.eth.treasury_tokens.USDC, owner=safe.account
    )

    safe.take_snapshot(tokens=[
        threepool.address, usdc.address, frax3pool.address
    ])

    safe.convex.unstake_all_and_withdraw_all(threepool)
    safe.convex.unstake_all_and_withdraw_all(frax3pool)

    bal_frax3pool = frax3pool.balanceOf(safe) * DUSTY
    safe.curve.withdraw_to_one_coin(frax3pool, bal_frax3pool, threepool)

    bal_3pool = threepool.balanceOf(safe) * DUSTY
    safe.curve.withdraw_to_one_coin(threepool, bal_3pool, usdc)

    # under 1.9m the loss is >~88k
    expected = 1_900_000e6
    balance_checker.verifyBalance(usdc, safe, expected)

    safe.print_snapshot()
    safe.post_safe_tx()
