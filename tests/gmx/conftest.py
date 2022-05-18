import pytest
from brownie import Contract, accounts
from brownie_tokens import MintableForkToken

from great_ape_safe import GreatApeSafe
from helpers.addresses import registry


@pytest.fixture
def dev():
    return GreatApeSafe(registry.arbitrum.badger_wallets.dev_multisig)


@pytest.fixture
def gmx(dev):
    dev.init_gmx()
    return dev.gmx


@pytest.fixture
def whale():
    return accounts.at("0xc5ed2333f8a2C351fCA35E5EBAdb2A82F5d254C3", force=True)


@pytest.fixture
def dai(dev, whale):
    dai = dev.contract("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")
    dai.transfer(dev, 100_000e18, {'from': whale})
    return dai


@pytest.fixture
def wbtc(dev, whale):
    wbtc = dev.contract(registry.arbitrum.treasury_tokens.WBTC)
    wbtc.transfer(dev, 10e8, {'from': whale})
    return wbtc


@pytest.fixture(autouse=True)
def test_whale_is_still_whale(whale, dai, wbtc):
    assert dai.balanceOf(whale) >= 10_000e18
    assert wbtc.balanceOf(whale) >= 10e8
