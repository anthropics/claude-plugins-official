// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console} from "forge-std/Script.sol";
import {Vault} from "../src/Vault.sol";

contract InteractScript is Script {
    function deposit(address vaultAddress, uint256 amount) public {
        vm.startBroadcast();
        Vault(vaultAddress).deposit{value: amount}();
        console.log("Deposited", amount, "wei");
        vm.stopBroadcast();
    }

    function withdraw(address vaultAddress, uint256 amount) public {
        vm.startBroadcast();
        Vault(vaultAddress).withdraw(amount);
        console.log("Withdrawn", amount, "wei");
        vm.stopBroadcast();
    }

    function withdrawAll(address vaultAddress) public {
        vm.startBroadcast();
        Vault(vaultAddress).withdrawAll();
        console.log("Withdrawn all funds");
        vm.stopBroadcast();
    }

    function pause(address vaultAddress) public {
        vm.startBroadcast();
        Vault(vaultAddress).pause();
        console.log("Vault paused");
        vm.stopBroadcast();
    }

    function unpause(address vaultAddress) public {
        vm.startBroadcast();
        Vault(vaultAddress).unpause();
        console.log("Vault unpaused");
        vm.stopBroadcast();
    }

    function status(address vaultAddress) public view {
        Vault vault = Vault(vaultAddress);

        console.log("=== Vault Status ===");
        console.log("Address:", vaultAddress);
        console.log("Total Deposits:", vault.totalDeposits());
        console.log("Vault Balance:", vault.vaultBalance());
        console.log("Paused:", vault.paused());
    }

    function checkBalance(address vaultAddress, address account) public view {
        Vault vault = Vault(vaultAddress);
        uint256 balance = vault.balanceOf(account);
        console.log("Balance of", account, ":", balance);
    }
}
