from great_ape_safe import GreatApeSafe
from helpers.addresses import r


VOTER = GreatApeSafe(r.badger_wallets.bvecvx_voting_multisig)
BAL = VOTER.contract(r.treasury_tokens.BAL)


def move_to_voter():
    safe = GreatApeSafe(r.badger_wallets.treasury_vault_multisig)

    VOTER.take_snapshot([BAL])
    safe.take_snapshot([BAL])
    safe.init_balancer()
    safe.balancer.claim(pool=r.balancer.B_20_BTC_80_BADGER)
    BAL.transfer(VOTER, BAL.balanceOf(safe), {'from': safe.account})

    VOTER.print_snapshot()
    safe.post_safe_tx()


def main():
    '''
    ref: https://github.com/aurafinance/aura-contracts-lite
    ref: https://dev.balancer.fi/references/error-codes
    ref: https://docs.aura.finance/developers/deployed-addresses
    kovan: https://whimsical-snowman-458.notion.site/Deployment-a5dc796b4923412c89b57d06de51141b
    '''
    wrapper = VOTER.contract(r.aura.wrapper)
    aura = VOTER.contract(r.treasury_tokens.AURA)
    aurabal = VOTER.contract(r.treasury_tokens.AURABAL)
    bpt_aurabal = r.balancer.bpt_aurabal  # pool_id: 0x3dd0843a028c86e0b760b1a76929d1c5ef93a2dd000200000000000000000249

    VOTER.init_balancer()
    VOTER.take_snapshot([BAL, aura, aurabal])

    BAL.approve(wrapper, BAL.balanceOf(VOTER))
    wrapper.deposit(
        BAL.balanceOf(VOTER),  # uint256 _amount
        wrapper.getMinOut(BAL.balanceOf(VOTER), 9950),  # uint256 _minOut
        True,  # bool _lock
        VOTER.balancer.gauge_factory.getPoolGauge(bpt_aurabal)  # address _stakeAddress
    )

    VOTER.post_safe_tx()
