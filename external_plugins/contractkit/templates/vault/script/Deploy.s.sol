// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {Vault} from "../src/Vault.sol";

contract DeployScript is Script {
    function run() public {
        vm.startBroadcast();

        Vault vault = new Vault();

        console.log("Vault deployed at:", address(vault));
        console.log("Admin:", msg.sender);

        vm.stopBroadcast();
    }
}
