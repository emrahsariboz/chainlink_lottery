import pytest
from scripts.deploy import deploy_lottery

from brownie import Lottery, accounts, config, network, exceptions
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)


@pytest.fixture(autouse=True)
def lottery():
    print("Testing...")
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    print("Deploying Smart Contract...")
    lottery = deploy_lottery()

    account = get_account()

    print(f"You are in {network.show_active()} network")

    return (lottery, account)
