source .venv/bin/activate
source .env
cd solidity_flasharb
echo "Generating ABI of arb contract"
rm -r build/contracts/
brownie compile contracts/arb.sol
cd ..

python main.py
