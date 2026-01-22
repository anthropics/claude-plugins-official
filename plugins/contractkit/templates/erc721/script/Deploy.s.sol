// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console} from "forge-std/Script.sol";
import {NFT} from "../src/NFT.sol";

contract DeployScript is Script {
    function run() public {
        string memory baseURI = vm.envOr("BASE_URI", string("https://example.com/metadata/"));

        vm.startBroadcast();

        NFT nft = new NFT("{{TOKEN_NAME}}", "{{TOKEN_SYMBOL}}", baseURI);

        console.log("NFT deployed at:", address(nft));
        console.log("Deployer:", msg.sender);
        console.log("Base URI:", baseURI);

        vm.stopBroadcast();
    }
}
