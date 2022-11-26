from lp_wrapper import LP
from token_wrapper import Token
from scipy import optimize

class BorrowSwapArb:
    def __init__(
        self,
        borrow_pool:LP,
        swap_pool:LP,
        borrow_token:Token,
        repay_token:Token
    ):
        assert (borrow_pool.token0.address, borrow_pool.token1.address) in \
            [(borrow_token.address, repay_token.address),(repay_token.address, borrow_token.address)], "Borrow pool needs to match borrow and repay tokens"
        assert (swap_pool.token0.address, swap_pool.token1.address) in \
            [(borrow_token.address, repay_token.address),(repay_token.address, borrow_token.address)], "Swap pool needs to match borrow and repay tokens"
        
        self.borrow_pool = borrow_pool
        self.swap_pool = swap_pool
        self.borrow_token = borrow_token
        self.repay_token = repay_token

        self.res = {
            "borrow_token": self.borrow_token,
            "repay_token": self.repay_token,
            "borrow_amount":0,             
            "swap_out_amount": 0,
            "repay_amount": 0,                        
            "profit_amount": 0            
        }
        self.on_init=True

    def refresh(self) -> bool:
        recalculate=False
        if self.on_init: 
            recalculate=True
            self.on_init=False
        if self.borrow_pool.get_reserves(): recalculate=True
        if self.swap_pool.get_reserves(): recalculate=True
        if recalculate: 
            self._calculate_arbitrage()
            return True
        else: return False

    def _calculate_arbitrage(self):
        
        max_borrow = self.borrow_pool.reserve_token0 if (self.borrow_token.address == self.borrow_pool.token0.address) \
                        else self.borrow_pool.reserve_token1
        bounds = (1, max_borrow)
        bracket = (0.001*max_borrow, 0.01*max_borrow)

        ##find optimal borrow amount to maximize profit (in repay tokens)
        opt = optimize.minimize_scalar(
            lambda x: -float(
                self.swap_pool.get_amount_out(self.borrow_token.address, x) -
                    self.borrow_pool.get_amount_in(self.repay_token.address, x)),
            method="bounded",
            bounds=bounds,
            bracket=bracket,
        )

        optim_borrow, optim_profit = int(opt.x), -int(opt.fun)
        
        if optim_profit > 0: 
            self.res.update(
                {                    
                    "borrow_amount": optim_borrow,
                    "swap_out_amount": self.swap_pool.get_amount_out(self.borrow_token.address, optim_borrow),
                    "repay_amount": self.borrow_pool.get_amount_in(self.repay_token.address, optim_borrow),
                    "profit_amount": optim_profit            
                }
            )
        else:
            self.res.update(
                {                    
                    "borrow_amount": 0,
                    "swap_out_amount": 0,
                    "repay_amount": 0,
                    "profit_amount": 0            
                }
            )














        





        
        


    
