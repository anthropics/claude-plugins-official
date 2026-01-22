// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console} from "forge-std/Script.sol";
import {Escrow} from "../src/Escrow.sol";

contract DeployScript is Script {
    function run() public {
        address payee = vm.envAddress("PAYEE_ADDRESS");
        address arbiter = vm.envAddress("ARBITER_ADDRESS");
        uint256 amount = vm.envUint("ESCROW_AMOUNT");

        vm.startBroadcast();

        Escrow escrow = new Escrow(payee, arbiter, amount);

        console.log("Escrow deployed at:", address(escrow));
        console.log("Payer:", msg.sender);
        console.log("Payee:", payee);
        console.log("Arbiter:", arbiter);
        console.log("Amount:", amount);

        vm.stopBroadcast();
    }
}
