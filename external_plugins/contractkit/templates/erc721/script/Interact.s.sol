// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {NFT} from "../src/NFT.sol";

contract InteractScript is Script {
    function mint(address nftAddress, address to) public {
        vm.startBroadcast();

        NFT nft = NFT(nftAddress);
        uint256 tokenId = nft.mint(to);

        console.log("Minted token", tokenId, "to", to);

        vm.stopBroadcast();
    }

    function checkOwner(address nftAddress, uint256 tokenId) public view {
        NFT nft = NFT(nftAddress);
        address owner = nft.ownerOf(tokenId);
        console.log("Owner of token", tokenId, ":", owner);
    }

    function checkBalance(address nftAddress, address account) public view {
        NFT nft = NFT(nftAddress);
        uint256 balance = nft.balanceOf(account);
        console.log("Balance of", account, ":", balance);
    }

    function grantMinter(address nftAddress, address account) public {
        vm.startBroadcast();

        NFT nft = NFT(nftAddress);
        nft.grantRole(nft.MINTER_ROLE(), account);

        console.log("Granted MINTER_ROLE to", account);

        vm.stopBroadcast();
    }

    function setBaseURI(address nftAddress, string memory newURI) public {
        vm.startBroadcast();

        NFT nft = NFT(nftAddress);
        nft.setBaseURI(newURI);

        console.log("Set base URI to:", newURI);

        vm.stopBroadcast();
    }
}
