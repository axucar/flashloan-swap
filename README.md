Idea: borrow tokenA from a liquidity pool LP1 with abundant tokenA, swap for tokenB at another pool LP2, and finally repay with tokenB at LP1. 

The interesting bits are in `main.py` and the solidity contract in `solidity_flasharb/contracts`. 
There are wrapper objects to represent tokens, LPs, and arbitrages:`token_wrapper.py, lp_wrapper.py, borrow_swap_arb.py`.
# How to use:

1. Run `install.sh` to setup python environment with packages needed 
2. Set up `.env` similar to `.env_example`
3. Confirm settings and contract addresses in `config.py` as desired, including setting `BROWNIE_NETWORK` 
4. Run `run.sh` 
