from brownie import ETH_ADDRESS

from helpers.addresses import registry


class Compound():
    def __init__(self, safe):
        self.safe = safe

        # tokens
        self.comp = safe.contract(registry.eth.treasury_tokens.COMP)

        # contracts
        self.comptroller = safe.contract(registry.eth.compound.comptroller)


    def _get_ctoken(self, underlying):
        for ctoken in self.comptroller.getAllMarkets():
            ctoken = self.safe.contract(ctoken)
            try:
                if underlying == ETH_ADDRESS:
                    if ctoken.symbol() == 'cETH':
                        return ctoken
                elif ctoken.underlying() == underlying.address:
                    if self.comptroller.mintGuardianPaused(ctoken):
                        # eg old cwbtc contract has been replaced by cwbtc2
                        continue
                    return ctoken
            except AttributeError:
                # $ceth has no underlying
                if ctoken.symbol() == 'cETH':
                    pass
                else:
                    # in case `AttributeError` stems from something else
                    raise
        # for loop did not find `underlying`
        raise


    def _enter_market(self, underlying):
        # https://compound.finance/docs/comptroller#enter-markets
        ctoken = self._get_ctoken(underlying)
        self.comptroller.enterMarkets([ctoken])
        # assert self.comptroller.getAccountLiquidity(self.safe)[0] == 0
        # assert self.comptroller.getAccountLiquidity(self.safe)[0] > 0


    def deposit(self, underlying, mantissa):
        # deposit `mantissa` amount of `underlying` into its respective compound's ctoken
        # https://compound.finance/docs/ctokens#mint
        ctoken = self._get_ctoken(underlying)
        underlying.approve(ctoken, mantissa)
        assert ctoken.mint(mantissa).return_value == 0


    def deposit_eth(self, mantissa):
        # deposit `mantissa` amount of $eth into its respective compound's ctoken
        # https://compound.finance/docs/ctokens#mint
        ctoken = self._get_ctoken(ETH_ADDRESS)
        bal_before = ctoken.balanceOf(self.safe)
        ctoken.mint({'from': self.safe.address, 'value': mantissa})
        assert ctoken.balanceOf(self.safe) > bal_before


    def withdraw(self, underlying, mantissa):
        # withdraw `mantissa` amount of `underlying` from its corresponding ctoken
        # https://compound.finance/docs/ctokens#redeem-underlying
        ctoken = self._get_ctoken(underlying)
        assert ctoken.redeemUnderlying(mantissa).return_value == 0


    def withdraw_eth(self, mantissa):
        # withdraw `mantissa` amount of $eth from its corresponding ctoken
        # https://compound.finance/docs/ctokens#redeem-underlying
        ctoken = self._get_ctoken(ETH_ADDRESS)
        assert ctoken.redeemUnderlying(mantissa).return_value == 0


    def withdraw_ctoken(self, ctoken, mantissa):
        # redeem `mantissa` amount of `ctoken` back into its underlying
        # https://compound.finance/docs/ctokens#redeem
        assert ctoken.redeem(mantissa).return_value == 0


    def borrow(self, underlying, borrow, mantissa):
        self._enter_market(underlying)
        ctoken = self._get_ctoken(borrow)
        ctoken.borrow(mantissa)


    def repay(self, underlying, mantissa=None):
        ctoken = self._get_ctoken(underlying)
        if mantissa:
            underlying.approve(ctoken, mantissa)
            ctoken.repayBorrow(mantissa)
        else:
            underlying.approve(ctoken, underlying.balanceOf(self.safe))
            ctoken.repayBorrow(2 ** 256 - 1)


    def repay_all(self, underlying):
        self.repay(underlying)


    def claim_all(self):
        # claim all $comp accrued by safe in all markets
        # https://compound.finance/docs/comptroller#claim-comp
        bal_before = self.comp.balanceOf(self.safe)
        self.comptroller.claimComp(self.safe)
        assert self.comp.balanceOf(self.safe) > bal_before


    def claim(self, underlyings):
        # convert each `underlying` in list `underlyings` to its corresponding
        # ctoken and claim all pending $comp for those ctokens in one call
        # instead of a list `underlyings` can also be a single asset
        # https://compound.finance/docs/comptroller#claim-comp
        if type(underlyings) != 'list':
            underlyings = [underlyings]
        ctokens = []
        for underlying in underlyings:
            ctoken = self._get_ctoken(underlying)
            ctokens.append(ctoken.address)
        assert len(ctokens) > 0
        bal_before = self.comp.balanceOf(self.safe)
        self.comptroller.claimComp(self.safe, ctokens)
        assert self.comp.balanceOf(self.safe) > bal_before
