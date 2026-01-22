// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {Escrow} from "../src/Escrow.sol";

contract InteractScript is Script {
    function fund(address escrowAddress) public {
        Escrow escrow = Escrow(escrowAddress);
        uint256 amount = escrow.amount();

        vm.startBroadcast();
        escrow.fund{value: amount}();
        console.log("Funded escrow with", amount, "wei");
        vm.stopBroadcast();
    }

    function release(address escrowAddress) public {
        vm.startBroadcast();
        Escrow(escrowAddress).release();
        console.log("Released funds to payee");
        vm.stopBroadcast();
    }

    function refund(address escrowAddress) public {
        vm.startBroadcast();
        Escrow(escrowAddress).refund();
        console.log("Refunded funds to payer");
        vm.stopBroadcast();
    }

    function dispute(address escrowAddress) public {
        vm.startBroadcast();
        Escrow(escrowAddress).dispute();
        console.log("Dispute initiated");
        vm.stopBroadcast();
    }

    function resolve(address escrowAddress, address winner) public {
        vm.startBroadcast();
        Escrow(escrowAddress).resolve(winner);
        console.log("Resolved dispute in favor of:", winner);
        vm.stopBroadcast();
    }

    function status(address escrowAddress) public view {
        Escrow escrow = Escrow(escrowAddress);

        console.log("=== Escrow Status ===");
        console.log("Address:", escrowAddress);
        console.log("Payer:", escrow.payer());
        console.log("Payee:", escrow.payee());
        console.log("Arbiter:", escrow.arbiter());
        console.log("Amount:", escrow.amount());
        console.log("Balance:", escrow.balance());
        console.log("State:", uint256(escrow.state()));
    }
}
