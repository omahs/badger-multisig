from brownie import chain


def test_deposit(dev, gmx, dai, wbtc):
    for token in [wbtc, dai]:
        gmx.deposit(token, token.balanceOf(dev))
