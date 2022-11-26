#!/usr/bin/env bash

# Create a virtual environment called .venv (here `python3` will refer to the Python3 version installed on your PC
# python3 -m venv .venv
# source ./.venv/bin/activate
# python3 -m pip install [package_name]

set -e

# Constants
VENV_PATH="./.venv"
PYTHON_VERSION="python3.10"

# Setup virtual env
rm -rf ${VENV_PATH}
virtualenv --quiet ${VENV_PATH} --python=${PYTHON_VERSION}
echo "Created virtual environment for ${PYTHON_VERSION}"

# Install dependencies
source ./.venv/bin/activate
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

pip install --quiet numpy 
pip install --quiet eth-brownie
pip install --quiet eth_abi
pip install --quiet requests
pip install --quiet web3
pip install --quiet flashbots
pip install --quiet --upgrade websockets
pip install --quiet vyper
pip install --quiet scipy
pip install --quiet networkx
pip install --quiet matplotlib
pip install --quiet pyqt5
pip install --quiet sigfig

echo "Base dependencies installed"
echo "Done!"


