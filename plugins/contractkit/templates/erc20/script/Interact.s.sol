// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console} from "forge-std/Script.sol";
import {Token} from "../src/Token.sol";

contract InteractScript is Script {
    function mint(address tokenAddress, address to, uint256 amount) public {
        vm.startBroadcast();

        Token token = Token(tokenAddress);
        token.mint(to, amount);

        console.log("Minted", amount, "tokens to", to);

        vm.stopBroadcast();
    }

    function checkBalance(address tokenAddress, address account) public view {
        Token token = Token(tokenAddress);
        uint256 balance = token.balanceOf(account);
        console.log("Balance of", account, ":", balance);
    }

    function grantMinter(address tokenAddress, address account) public {
        vm.startBroadcast();

        Token token = Token(tokenAddress);
        token.grantRole(token.MINTER_ROLE(), account);

        console.log("Granted MINTER_ROLE to", account);

        vm.stopBroadcast();
    }
}
