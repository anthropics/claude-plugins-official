// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console} from "forge-std/Script.sol";
import {Token} from "../src/Token.sol";

contract DeployScript is Script {
    function run() public {
        vm.startBroadcast();

        Token token = new Token("{{TOKEN_NAME}}", "{{TOKEN_SYMBOL}}");

        console.log("Token deployed at:", address(token));
        console.log("Deployer:", msg.sender);

        vm.stopBroadcast();
    }
}
