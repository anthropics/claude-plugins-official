// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @title {{PROJECT_NAME}}
/// @notice Simple ETH vault with deposit and withdraw functionality
/// @dev Uses ReentrancyGuard and AccessControl for security
contract Vault is ReentrancyGuard, AccessControl {
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    mapping(address => uint256) private _balances;
    uint256 private _totalDeposits;
    bool public paused;

    event Deposited(address indexed account, uint256 amount);
    event Withdrawn(address indexed account, uint256 amount);
    event Paused(address account);
    event Unpaused(address account);

    error InsufficientBalance(uint256 requested, uint256 available);
    error ZeroAmount();
    error TransferFailed();
    error ContractPaused();

    modifier whenNotPaused() {
        if (paused) revert ContractPaused();
        _;
    }

    /// @notice Creates a new vault with the deployer as admin
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
    }

    /// @notice Deposits ETH into the vault
    /// @dev Sender's balance is credited with the deposited amount
    function deposit() external payable whenNotPaused {
        if (msg.value == 0) revert ZeroAmount();

        _balances[msg.sender] += msg.value;
        _totalDeposits += msg.value;

        emit Deposited(msg.sender, msg.value);
    }

    /// @notice Withdraws ETH from the vault
    /// @param amount The amount of ETH to withdraw in wei
    function withdraw(uint256 amount) external nonReentrant whenNotPaused {
        if (amount == 0) revert ZeroAmount();

        uint256 balance = _balances[msg.sender];
        if (amount > balance) {
            revert InsufficientBalance(amount, balance);
        }

        _balances[msg.sender] = balance - amount;
        _totalDeposits -= amount;

        (bool success,) = msg.sender.call{value: amount}("");
        if (!success) revert TransferFailed();

        emit Withdrawn(msg.sender, amount);
    }

    /// @notice Withdraws all ETH from the vault for the sender
    function withdrawAll() external nonReentrant whenNotPaused {
        uint256 balance = _balances[msg.sender];
        if (balance == 0) revert ZeroAmount();

        _balances[msg.sender] = 0;
        _totalDeposits -= balance;

        (bool success,) = msg.sender.call{value: balance}("");
        if (!success) revert TransferFailed();

        emit Withdrawn(msg.sender, balance);
    }

    /// @notice Pauses the vault
    /// @dev Only callable by addresses with PAUSER_ROLE
    function pause() external onlyRole(PAUSER_ROLE) {
        paused = true;
        emit Paused(msg.sender);
    }

    /// @notice Unpauses the vault
    /// @dev Only callable by addresses with PAUSER_ROLE
    function unpause() external onlyRole(PAUSER_ROLE) {
        paused = false;
        emit Unpaused(msg.sender);
    }

    /// @notice Returns the balance of an account
    /// @param account The address to check
    /// @return The balance in wei
    function balanceOf(address account) external view returns (uint256) {
        return _balances[account];
    }

    /// @notice Returns the total deposits in the vault
    /// @return The total deposits in wei
    function totalDeposits() external view returns (uint256) {
        return _totalDeposits;
    }

    /// @notice Returns the actual ETH balance of the vault contract
    /// @return The contract balance in wei
    function vaultBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
