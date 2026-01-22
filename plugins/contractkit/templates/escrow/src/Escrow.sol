// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/// @title {{PROJECT_NAME}}
/// @notice Three-party escrow contract with release, refund, and dispute resolution
/// @dev Uses ReentrancyGuard to prevent reentrancy attacks
contract Escrow is ReentrancyGuard {
    enum State {
        Created,
        Funded,
        Released,
        Refunded,
        Disputed
    }

    address public immutable payer;
    address public immutable payee;
    address public immutable arbiter;
    uint256 public immutable amount;

    State public state;

    event Funded(uint256 amount);
    event Released(uint256 amount);
    event Refunded(uint256 amount);
    event Disputed(address initiator);
    event Resolved(address winner, uint256 amount);

    error InvalidState(State expected, State actual);
    error Unauthorized();
    error InvalidAmount();
    error TransferFailed();

    modifier onlyPayer() {
        if (msg.sender != payer) revert Unauthorized();
        _;
    }

    modifier onlyPayee() {
        if (msg.sender != payee) revert Unauthorized();
        _;
    }

    modifier onlyArbiter() {
        if (msg.sender != arbiter) revert Unauthorized();
        _;
    }

    modifier onlyParty() {
        if (msg.sender != payer && msg.sender != payee) revert Unauthorized();
        _;
    }

    modifier inState(State expected) {
        if (state != expected) revert InvalidState(expected, state);
        _;
    }

    /// @notice Creates a new escrow agreement
    /// @param _payee The address that will receive funds on release
    /// @param _arbiter The address that can resolve disputes
    /// @param _amount The expected escrow amount in wei
    constructor(address _payee, address _arbiter, uint256 _amount) {
        if (_payee == address(0) || _arbiter == address(0)) revert Unauthorized();
        if (_amount == 0) revert InvalidAmount();

        payer = msg.sender;
        payee = _payee;
        arbiter = _arbiter;
        amount = _amount;
        state = State.Created;
    }

    /// @notice Funds the escrow with the agreed amount
    /// @dev Must send exactly the agreed amount
    function fund() external payable onlyPayer inState(State.Created) {
        if (msg.value != amount) revert InvalidAmount();

        state = State.Funded;
        emit Funded(msg.value);
    }

    /// @notice Releases funds to the payee
    /// @dev Only payer can release, escrow must be funded
    function release() external onlyPayer inState(State.Funded) nonReentrant {
        state = State.Released;

        (bool success,) = payee.call{value: amount}("");
        if (!success) revert TransferFailed();

        emit Released(amount);
    }

    /// @notice Refunds funds to the payer
    /// @dev Only payee can refund, escrow must be funded
    function refund() external onlyPayee inState(State.Funded) nonReentrant {
        state = State.Refunded;

        (bool success,) = payer.call{value: amount}("");
        if (!success) revert TransferFailed();

        emit Refunded(amount);
    }

    /// @notice Initiates a dispute
    /// @dev Either payer or payee can dispute, escrow must be funded
    function dispute() external onlyParty inState(State.Funded) {
        state = State.Disputed;
        emit Disputed(msg.sender);
    }

    /// @notice Resolves a dispute by sending funds to the winner
    /// @dev Only arbiter can resolve, escrow must be disputed
    /// @param winner The address to receive the escrowed funds
    function resolve(address winner) external onlyArbiter inState(State.Disputed) nonReentrant {
        if (winner != payer && winner != payee) revert Unauthorized();

        if (winner == payer) {
            state = State.Refunded;
        } else {
            state = State.Released;
        }

        (bool success,) = winner.call{value: amount}("");
        if (!success) revert TransferFailed();

        emit Resolved(winner, amount);
    }

    /// @notice Returns the current balance of the escrow
    function balance() external view returns (uint256) {
        return address(this).balance;
    }
}
