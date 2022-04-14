# 0.019
# 190000000000000000

from brownie import Lottery, accounts, config, network, exceptions
import pytest
from regex import E
from scripts.deploy import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)
from brownie.network.account import PublicKeyAccount
from web3 import Web3
import time


@pytest.fixture()
def lottery():
    print("Testing...")
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    print("Deploying Smart Contract...")
    lottery = deploy_lottery()

    account = get_account()

    return (lottery, account)


def test_get_entract_fee(lottery):

    lottery, account = lottery

    # Initial Price
    # 200000000000
    # 2000$ 1 ETH
    # 50$ ? ETH

    # ETH = 50 / 2000
    # 0.25
    # Expected

    expected = Web3.toWei(0.25, "ether")
    entrace_fee = lottery.getEntranceFee()

    # Assert

    assert expected == entrace_fee


def test_entrance(lottery):
    lottery, account = lottery
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": account, "value": lottery.getEntranceFee()})


def test_if_they_can_enter(lottery):
    lottery, account = lottery

    tx = lottery.startLottery({"from": account})

    tx.wait(1)

    lottery.enter({"from": account, "value": lottery.getEntranceFee()})

    tx.wait(1)

    assert lottery.players(0) == account


def test_if_they_can_end(lottery):
    lottery, account = lottery

    lottery.startLottery({"from": account})

    lottery.enter({"from": account, "value": lottery.getEntranceFee()})

    fund_with_link(lottery)

    lottery.endLottery({"from": account})

    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly(lottery):

    lottery, account = lottery

    lottery.startLottery({"from": account})

    lottery.enter({"from": account, "value": lottery.getEntranceFee()})

    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})

    fund_with_link(lottery)

    transaction = lottery.endLottery({"from": account})

    request_id = transaction.events["RequestRandomness"]["requestId"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )

    starting_balance = account.balance()

    balance_of_lottery = lottery.balance()

    assert lottery.recentWinner() == account

    assert lottery.balance() == 0

    assert account.balance() == balance_of_lottery + starting_balance
