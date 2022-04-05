from decimal import Decimal

import eth_abi
from brownie import interface, network
from web3 import Web3, HTTPProvider

from great_ape_safe import GreatApeSafe
from helpers.addresses import registry


# the following constants were taken from existing txs that bridge $badger, eg:
# https://etherscan.io/tx/0x55d1919669134e9d01a43ba546f517c9f08a285cf0053eb1218c41818ca8199b
# https://etherscan.io/tx/0x7a035f228e9cc0c40b0c7c22c8fac9d25d90f12f51fa5f2398f790c660fee0b6
# https://etherscan.io/tx/0xd07ab58e31045ed7b2eca18e5c2b286f1d45c3d15681654d13b62f1eef9766b2
# real way to do it is use their sdk and do something similar to what is
# being done here for `submissionPriceWei` and `maxGas`:
# https://github.com/OffchainLabs/arbitrum-tutorials/blob/master/packages/greeter/scripts/exec.js#L92-L147
# https://github.com/OffchainLabs/arbitrum-sdk/blob/master/src/lib/message/L1ToL2MessageGasEstimator.ts
MAX_SUBMISSION_COST = 1651721706175
MAX_GAS = 143898


def main(mantissa):
    """
    bridge mantissa amount of $badger over from mainnet to the arbitrum techops
    msig
    """

    mantissa = Decimal(mantissa)

    safe = GreatApeSafe(registry.eth.badger_wallets.treasury_ops_multisig)
    badger = interface.ERC20(
        registry.eth.treasury_tokens.BADGER, owner=safe.account
    )
    l1_router = interface.IL1GatewayRouter(
        registry.eth.arbitrum.l1_gateway_router, owner=safe.account
    )
    l1_gateway = interface.IL1ERC20Gateway(
        l1_router.getGateway(badger), owner=safe.account
    )

    l2 = Web3(HTTPProvider(network.main.CONFIG.networks['arbitrum']['host']))
    gas_price_bid = l2.eth.gas_price
    data = eth_abi.encode_abi(
        ['uint256', 'bytes'], (MAX_SUBMISSION_COST, b'')
    ).hex()

    print(l1_gateway.getOutboundCalldata(
        badger,
        safe,
        registry.arbitrum.badger_wallets.techops_multisig,
        mantissa,
        b''
    ))

    badger.approve(l1_gateway, mantissa)
    l1_router.outboundTransfer(
        badger,
        registry.arbitrum.badger_wallets.techops_multisig,
        mantissa,
        MAX_GAS,
        gas_price_bid,
        data,
        {'value': MAX_SUBMISSION_COST + (MAX_GAS * gas_price_bid)}
    )

    safe.post_safe_tx(call_trace=True)


def retrieve_on_arbitrum():
    # note that this needs to be called on arbitrum, not mainnet
    # currently i dont see a way to do this scripted (at least not without
    # completely integrating their sdk)
    # best way is probably to use the ui to create the following calldata:
    # createRetryableTicket(address,uint256,uint256,address,address,uint256,uint256,bytes)
    # https://developer.offchainlabs.com/docs/sol_contract_docs/md_docs/arb-bridge-eth/bridge/inbox#createretryableticketaddress-destaddr-uint256-l2callvalue-uint256-maxsubmissioncost-address-excessfeerefundaddress-address-callvaluerefundaddress-uint256-maxgas-uint256-gaspricebid-bytes-data-%E2%86%92-uint256-external
    calldata = None

    safe = GreatApeSafe(registry.arbitrum.badger_wallets.techops_multisig)
    safe.account.transfer(
        registry.arbitrum.arbitrum.arb_retryable_tx, data=calldata
    )
    safe.post_safe_tx(call_trace=True)
