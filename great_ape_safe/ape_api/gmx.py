from secrets import token_bytes
from helpers.addresses import registry

class GMX:
    def __init__(self, safe):
        self.safe = safe
        # tokens
        self.glp = safe.contract("0x4277f8F2c384827B5273592FF7CeBd9f2C1ac258")
        # contracts
        self.reward_router = safe.contract("0xA906F338CB21815cBc4Bc87ace9e68c87eF8d8F1")
        self.glp_manager = safe.contract("0x321F653eED006AD1C29D174e17d96351BDe22649")
        self.staked_glp = safe.contract("0x1aDDD80E6039594eE970E5872D247bf0414C8903")
        self.vault = safe.contract("0x489ee077994B6658eAfA855C308275EAd8097C4A")


    def get_glp_price(self, side="buy"):
        aum = self.glp_manager.getAum(True if side == "buy" else False)
        supply =  self.glp.totalSupply()
        return aum / supply


    def deposit(self, token, mantissa):
        # https://gmxio.gitbook.io/gmx/contracts#buying-selling-glp
        # deposit `mantissa` `token` to mint and stake glp
        # todo: check if token is a valid token
        token.approve(self.reward_router, mantissa)
        token.approve(self.glp_manager, mantissa)

        # `getMinPrice` accounts for slippage?
        min_glp = (mantissa * self.get_glp_price()) / self.vault.getMinPrice(token)
        # this requires price feed for `token`/glp pair
        min_glp_usd = 0

        bal_before_glp = self.staked_glp.balanceOf(self.safe)

        self.reward_router.mintAndStakeGlp(token, mantissa, min_glp_usd, min_glp)

        assert self.staked_glp.balanceOf(self.safe) > bal_before_glp
