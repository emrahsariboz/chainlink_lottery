// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";

contract Lottery is VRFConsumerBase, Ownable {
    uint256 public usdEntranceFee;
    address payable[] public players;
    AggregatorV3Interface internal ethUsdPriceFeed;
    uint256 public fee;
    bytes32 public keyHash;
    address payable public recentWinner;

    event RequestRandomness(bytes32 requestId);

    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }

    LOTTERY_STATE public lottery_state;

    address public setAccount;

    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyhash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntranceFee = 50 * (10**18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED;
        fee = _fee;
        keyHash = _keyhash;
    }

    function enter() public payable {
        // 50$ minimum!
        require(lottery_state == LOTTERY_STATE.OPEN);
        require(msg.value >= getEntranceFee(), "Not enought ETH!");
        players.push(payable(msg.sender));
    }

    // Convert the entrance fee, which is 50$ into wei.
    // To do so:
    // Get the current ETH - dollar rate
    // 3500$ is 1 ETH
    // 50 is ?

    // ? ==> 50 / 3500$.
    // However, solidity does not support decimals.
    // So: 50 * (10**18)
    // Eth already has 10**18
    // So we add another 10**18 to 50$!
    // Resulting value has 10**18 decimals.

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();

        uint256 adjustedPrice = uint256(price) * 10**10;

        uint256 costToEnter = (usdEntranceFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Can't start a new lottery yet!"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    // Request random number from chaninlink node
    // Repsonse will be received by our contract
    function endLottery() public onlyOwner {
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;

        // requestID -->
        bytes32 requestId = requestRandomness(keyHash, fee);

        emit RequestRandomness(requestId);
    }

    // Received callback once the result is ready!
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "You arent there yet!"
        );

        require(_randomness > 0, "Random-not-found");

        uint256 indexOfWinner = _randomness % players.length;
        recentWinner = players[indexOfWinner];

        recentWinner.transfer(address(this).balance);

        // Reset For New Lottery
        players = new address payable[](0);

        lottery_state = LOTTERY_STATE.CLOSED;
    }
}
