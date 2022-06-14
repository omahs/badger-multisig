from great_ape_safe import GreatApeSafe
from helpers.addresses import r


def main():
    '''
    ref: https://github.com/aurafinance/aura-contracts-lite
    ref: https://dev.balancer.fi/references/error-codes
    ref: https://docs.aura.finance/developers/deployed-addresses
    kovan: https://whimsical-snowman-458.notion.site/Deployment-a5dc796b4923412c89b57d06de51141b
    '''
    safe = GreatApeSafe(r.badger_wallets.treasury_vault_multisig)
    wrapper = safe.contract(r.aura.wrapper)
    depositor = safe.contract(r.aura.depositor)
    bal = safe.contract(r.treasury_tokens.BAL)
    weth = safe.contract(r.treasury_tokens.WETH)
    bpt_aurabal = r.balancer.bpt_aurabal  # pool_id 0x3dd0843a028c86e0b760b1a76929d1c5ef93a2dd000200000000000000000249

    safe.init_balancer()
    safe.take_snapshot([bal, weth])

    bal.approve(wrapper, bal.balanceOf(safe))
    wrapper.deposit(
        bal.balanceOf(safe),  # uint256 _amount
        wrapper.getMinOut(bal.balanceOf(safe), 9950),  # uint256 _minOut
        True,  # bool _lock
        safe.balancer.gauge_factory.getPoolGauge(bpt_aurabal)  # address _stakeAddress
    )

    safe.print_snapshot()
    safe.post_safe_tx()

