from fractions import Fraction
import brownie
from token_wrapper import Token
import time
from sigfig import round

class LP:
    def __init__(
        self,
        address:str,
        tokens: list[Token] = [],
        name="SushiSwap",
        fee=Fraction(3, 1000)
    ):
        print(f"\nInitializing LP:{name}")
        self.fee = fee
        self.address = address
        self.name=name  
                
        try:
            self.contract = brownie.Contract(address)
        except:        
            self.contract = brownie.Contract.from_explorer(address)
        
        assert len(tokens) == 2, f"Expected 2 tokens, found {len(tokens)}"
        if (tokens[0].address == self.contract.token0()) and (tokens[1].address == self.contract.token1()):
            self.token0 = tokens[0]
            self.token1 = tokens[1]
        elif (tokens[1].address == self.contract.token0()) and (tokens[0].address == self.contract.token0()):
            self.token0 = tokens[1]
            self.token1 = tokens[0]    
        else:
            raise Exception("tokens list does not match LP tokens. Please double check tokens param")
    
        self.reserve_token0, self.reserve_token1 = self.contract.getReserves()[0:2]                
        print(f"Init Reserves for [{self.name}]")
        self.print_reserve_ratios()                

    #returns required input amount of token_in, in order to receive an output amount of other asset 
    def get_amount_in(self, token_in_address:str, amount_out:int) -> int:    
        assert token_in_address in (self.token0.address, self.token1.address), "Provided token_in does not match LP tokens"

        (reserve_in, reserve_out) = (self.reserve_token0, self.reserve_token1) \
                if (token_in_address == self.token0.address) else (self.reserve_token1, self.reserve_token0) 

        numerator = reserve_in * amount_out * self.fee.denominator
        denominator = (reserve_out - amount_out) * (self.fee.denominator - self.fee.numerator)
        return numerator // denominator + 1

    #given an input amount of token_in, returns the maximum output amount of the other asset
    def get_amount_out(self, token_in_address:str, amount_in: int) -> int:        
        assert token_in_address in (self.token0.address, self.token1.address), "Provided token_in does not match LP tokens"

        (reserve_in, reserve_out) = (self.reserve_token0, self.reserve_token1) \
                if (token_in_address == self.token0.address) else (self.reserve_token1, self.reserve_token0) 
        
        amount_in_with_fee = amount_in * (self.fee.denominator - self.fee.numerator)
        numerator = amount_in_with_fee * reserve_out
        denominator = reserve_in * self.fee.denominator + amount_in_with_fee
        return numerator // denominator
    
    ##refresh reserve values
    def get_reserves(self) -> bool:
        # record the last time this LP was updated
        self.update_timestamp = time.monotonic()

        try:
            result = self.contract.getReserves()[0:2]            
            if (self.reserve_token0, self.reserve_token1) != result[0:2]:                
                self.reserve_token0, self.reserve_token1 = result[0:2]
                print(f"\nUpdating Reserves for [{self.name}]")
                self.print_reserve_ratios()                
                return True
            else:
                return False
        except Exception as e:
            print(f"LP: exception at get_reserves for {self.name} LP: {e}")

    def print_reserve_ratios(self):
        print(f"{self.token0.symbol}/{self.token1.symbol} Reserve Ratio: " + \
            f"{round((self.reserve_token0/10**self.token0.decimals) / (self.reserve_token1/10**self.token1.decimals), 4)}")
        print(f"{self.token1.symbol}/{self.token0.symbol} Reserve Ratio: " + \
            f"{round((self.reserve_token1/10**self.token1.decimals) / (self.reserve_token0/10**self.token0.decimals), 4)}")
        print(f"{self.token0.symbol} Reserves: " + \
            f"{round(self.reserve_token0/10**self.token0.decimals,4)}")
        print(f"{self.token1.symbol} Reserves: " + \
            f"{round(self.reserve_token1/10**self.token1.decimals,4)}")