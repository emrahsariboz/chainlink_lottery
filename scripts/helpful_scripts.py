from os import link
from brownie import (
    Contract,
    network,
    accounts,
    config,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    interface,
)
from web3 import Web3
import math


FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-gui-2"]


def get_account(index=None, id=None):

    if index:
        return accounts[index]

    if id:

        return accounts.load(id)

    if (
        network.show_active() == "development"
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]

    return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """
    Checks if development network exists and returns addresses related
    to VRF coordinator, etc if true,

    else deploys mock version of that contract and returns the address of it.

    Args:
        contract_name

    Returns:
        browmnie.network.contract.ProjectContract: The most recent version.
    """

    contract_type = contract_to_mock[contract_name]

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        # Address
        # Already deployed, so retrieve contract object with abi.
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )

    return contract


DECIMALS = 8
INITIAL_VALUE = 2 * math.pow(10, 10)


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token, {"from": account})
    print("Deployed!")


def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):
    account = account if account else get_account()

    link_token = link_token if link_token else get_contract("link_token")

    tx = link_token.transfer(contract_address, amount, {"from": account})

    # link_token_contract = interface.LinkTokenInterface(link_token.address)

    # tx = link_token_contract.transfer(contract_address, amount, {"from": account})
    tx.wait(1)

    print("Fund contract")

    return tx