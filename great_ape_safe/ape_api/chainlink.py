from brownie import interface
from helpers.addresses import registry


class Chainlink:
    def __init__(self, safe):
        self.safe = safe

        # contracts
        self.relayer = self.safe.contract(
            registry.eth.chainlink.upkeep_registration_requests,
            interface.IUpkeepRegistrationRequests
        )
        self.feed_registry = self.safe.contract(
            registry.eth.chainlink.feed_registry, interface.IFeedRegistry
        )

        # tokens
        self.link = interface.ILinkToken(
            registry.eth.treasury_tokens.LINK, owner=safe.account
        )

    # https://github.com/smartcontractkit/chainlink/blob/develop/contracts/src/v0.8/Denominations.sol
    ETH_HEX = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'
    BTC_HEX = '0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'
    USD_HEX = '0x' + hex(840)[2:].zfill(40)
    GBP_HEX = '0x' + hex(826)[2:].zfill(40)
    EUR_HEX = '0x' + hex(978)[2:].zfill(40)
    JPY_HEX = '0x' + hex(392)[2:].zfill(40)
    KRW_HEX = '0x' + hex(410)[2:].zfill(40)
    CNY_HEX = '0x' + hex(156)[2:].zfill(40)
    AUD_HEX = '0x' + hex(36)[2:].zfill(40)
    CAD_HEX = '0x' + hex(124)[2:].zfill(40)
    CHF_HEX = '0x' + hex(756)[2:].zfill(40)
    ARS_HEX = '0x' + hex(32)[2:].zfill(40)
    PHP_HEX = '0x' + hex(608)[2:].zfill(40)
    NZD_HEX = '0x' + hex(554)[2:].zfill(40)
    SGD_HEX = '0x' + hex(702)[2:].zfill(40)
    NGN_HEX = '0x' + hex(566)[2:].zfill(40)
    ZAR_HEX = '0x' + hex(710)[2:].zfill(40)
    RUB_HEX = '0x' + hex(643)[2:].zfill(40)
    INR_HEX = '0x' + hex(356)[2:].zfill(40)
    BRL_HEX = '0x' + hex(986)[2:].zfill(40)


    def register_upkeep(
        self, name, contract_addr, gas_limit, link_mantissa, admin_addr=None
    ):
        '''
        ref: https://github.com/smartcontractkit/keeper/blob/master/contracts/UpkeepRegistrationRequests.sol
        '''

        admin_addr = self.safe.address if not admin_addr else admin_addr

        data = self.relayer.register.encode_input(
            name, # string memory name,
            b'', # bytes calldata encryptedEmail,
            contract_addr, # address upkeepContract,
            gas_limit, # uint32 gasLimit,
            admin_addr, # address adminAddress,
            b'', # bytes calldata checkData,
            link_mantissa, # uint96 amount,
            0 # uint8 source
        )

        self.link.transferAndCall(self.relayer, link_mantissa, data)
