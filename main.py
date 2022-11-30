import time
import os
import json
from fractions import Fraction
from brownie import accounts, network, Contract, web3, chain
from sigfig import round

from token_wrapper import Token
from lp_wrapper import LP
from borrow_swap_arb import BorrowSwapArb
import config as cfg

os.environ["ETHERSCAN_TOKEN"] = os.getenv("ETHERSCAN_API_KEY")
network.connect(cfg.BROWNIE_NETWORK)

player = accounts.add(private_key=os.getenv("ETH_PK")) 
arb_contract = Contract.from_abi(name="",address=cfg.ARB_CONTRACT_ADDRESS,abi=json.load(open(cfg.ARB_CONTRACT_ABI))["abi"])

ether_token = Token(address=cfg.WETH_CONTRACT_ADDRESS,oracle_address=cfg.ETH_CHAINLINK)
token_a = Token(address=cfg.A_CONTRACT_ADDRESS,oracle_address=cfg.A_CHAINLINK_ADDRESS)
token_b = Token(address=cfg.B_CONTRACT_ADDRESS,oracle_address=cfg.B_CHAINLINK_ADDRESS)
    
pool1 = LP(
    address=cfg.POOL1_CONTRACT_ADDRESS,
    name=cfg.POOL1_NAME,
    tokens=[token_a, token_b],
    fee=Fraction(3, 1000))
pool2 = LP(
    address=cfg.POOL2_CONTRACT_ADDRESS,        
    tokens=[token_a, token_b],
    name=cfg.POOL2_NAME,        
    fee=Fraction(3, 1000))
borrow_b_from_pool1 = BorrowSwapArb(
    borrow_pool=pool1,
    swap_pool=pool2,
    borrow_token=token_b,
    repay_token=token_a        
)
borrow_b_from_pool2 = BorrowSwapArb(
    borrow_pool=pool2,
    swap_pool=pool1,
    borrow_token=token_b,
    repay_token=token_a        
)
arb_list = [borrow_b_from_pool1, borrow_b_from_pool2] 

while True:
    for arb in arb_list:        
        arb.refresh()

        if arb.res["borrow_amount"] > 0:

            arb_profit_usd = arb.res["profit_amount"]/(10 ** arb.res["repay_token"].decimals)*arb.res["repay_token"].price                

            print("\nARB STEPS:" \
                f"\nBorrow {arb.res['borrow_amount']/(10**arb.res['borrow_token'].decimals):.2f} {arb.res['borrow_token'].symbol} on {arb.borrow_pool.name}," \
                f"\nSwap for {arb.res['swap_out_amount']/(10 ** arb.res['repay_token'].decimals):.2f} {arb.res['repay_token'].symbol} on {arb.swap_pool.name}," \
                f"\nRepay for {arb.res['repay_amount']/(10 ** arb.res['repay_token'].decimals):.2f} {arb.res['repay_token'].symbol} on {arb.borrow_pool.name}," \
                f"\nProfit {arb.res['profit_amount']/(10 ** arb.res['repay_token'].decimals):.2f} {arb.res['repay_token'].symbol} (${arb_profit_usd:.2f})\n" \
            )

            if chain.id == 1337: ##forked dev network
                last_base_fee = 30*(10**9)
                last_priority_fee = cfg.PRIORITY_FEE
            else:                ##live network
                last_base_fee = chain.base_fee
                last_priority_fee = web3.eth.max_priority_fee

            borrow_pool_amounts = [arb.res['borrow_amount'],0] if (arb.borrow_token.address == arb.borrow_pool.token0.address) \
                else [0, arb.res['borrow_amount']]
            swap_pool_amounts = [0, arb.res['swap_out_amount']] if (arb.borrow_token.address == arb.borrow_pool.token0.address) \
                else [arb.res['swap_out_amount'], 0]
            
            web3_f = web3.eth.contract(address = arb_contract.address, abi = arb_contract.abi)
            est_gas_usage = web3_f.functions.flash_borrow_to_swap(arb.borrow_pool.address,
                    borrow_pool_amounts,
                    arb.swap_pool.address,
                    swap_pool_amounts,
                    arb.res["repay_amount"]).estimateGas({'from':player.address})
            estimated_cost_usd = est_gas_usage*((last_base_fee+last_priority_fee)/10**18)*ether_token.price
            print(f"Estimated gas usage (web3.py): {est_gas_usage} wei")
            print(f"Base Fee: {last_base_fee/10**9} gwei, Priority Fee: {last_priority_fee/10**9} gwei, Estimated tx cost: ${estimated_cost_usd:.2f}")
            
            if arb_profit_usd >= 2*estimated_cost_usd and not cfg.DRY_RUN:

                print("Executing arbitrage...")
                try:
                    tx_params = {
                        "from":player.address,
                        "chainId": chain.id,
                        "gas": cfg.TX_GAS_LIMIT,
                        "nonce": player.nonce,
                        "maxFeePerGas": int(1.15 * last_base_fee),
                        "maxPriorityFeePerGas": max(cfg.PRIORITY_FEE, last_priority_fee),                        
                    }
                    arb_contract.flash_borrow_to_swap(
                        arb.borrow_pool.address,
                        borrow_pool_amounts,
                        arb.swap_pool.address,
                        swap_pool_amounts,
                        arb.res["repay_amount"],
                        tx_params,
                    )

                except Exception as e:
                    print(f"Failed to execute arb:{e}")
                finally:
                    break

    try:
        token_a.update_price()
        token_b.update_price()
        ether_token.update_price()
    except Exception as e:
        print(f"Failed to update prices: {e}")

    time.sleep(5)
    continue


