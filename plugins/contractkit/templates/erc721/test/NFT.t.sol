// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {NFT} from "../src/NFT.sol";

contract NFTTest is Test {
    NFT public nft;
    address public admin;
    address public minter;
    address public user;

    string constant NAME = "{{TOKEN_NAME}}";
    string constant SYMBOL = "{{TOKEN_SYMBOL}}";
    string constant BASE_URI = "https://example.com/metadata/";

    function setUp() public {
        admin = address(this);
        minter = makeAddr("minter");
        user = makeAddr("user");

        nft = new NFT(NAME, SYMBOL, BASE_URI);
    }

    function test_Name() public view {
        assertEq(nft.name(), NAME);
    }

    function test_Symbol() public view {
        assertEq(nft.symbol(), SYMBOL);
    }

    function test_AdminHasMinterRole() public view {
        assertTrue(nft.hasRole(nft.MINTER_ROLE(), admin));
    }

    function test_AdminHasAdminRole() public view {
        assertTrue(nft.hasRole(nft.DEFAULT_ADMIN_ROLE(), admin));
    }

    function test_MinterCanMint() public {
        uint256 tokenId = nft.mint(user);
        assertEq(tokenId, 0);
        assertEq(nft.ownerOf(0), user);
        assertEq(nft.balanceOf(user), 1);
    }

    function test_MintIncrementsTokenId() public {
        nft.mint(user);
        nft.mint(user);
        uint256 tokenId = nft.mint(user);
        assertEq(tokenId, 2);
        assertEq(nft.totalSupply(), 3);
    }

    function test_GrantMinterRole() public {
        nft.grantRole(nft.MINTER_ROLE(), minter);
        assertTrue(nft.hasRole(nft.MINTER_ROLE(), minter));

        vm.prank(minter);
        uint256 tokenId = nft.mint(user);
        assertEq(nft.ownerOf(tokenId), user);
    }

    function test_RevertWhen_NonMinterMints() public {
        vm.prank(user);
        vm.expectRevert();
        nft.mint(user);
    }

    function test_RevokeMinterRole() public {
        nft.grantRole(nft.MINTER_ROLE(), minter);
        nft.revokeRole(nft.MINTER_ROLE(), minter);
        assertFalse(nft.hasRole(nft.MINTER_ROLE(), minter));
    }

    function test_Transfer() public {
        nft.mint(admin);
        nft.transferFrom(admin, user, 0);
        assertEq(nft.ownerOf(0), user);
    }

    function test_TokenURI() public {
        nft.mint(user);
        assertEq(nft.tokenURI(0), string.concat(BASE_URI, "0"));
    }

    function test_SetBaseURI() public {
        string memory newURI = "https://new.example.com/";
        nft.setBaseURI(newURI);
        nft.mint(user);
        assertEq(nft.tokenURI(0), string.concat(newURI, "0"));
    }

    function test_RevertWhen_NonAdminSetsBaseURI() public {
        vm.prank(user);
        vm.expectRevert();
        nft.setBaseURI("https://malicious.com/");
    }

    function test_Approve_And_TransferFrom() public {
        nft.mint(admin);
        nft.approve(minter, 0);

        vm.prank(minter);
        nft.transferFrom(admin, user, 0);
        assertEq(nft.ownerOf(0), user);
    }

    function test_TotalSupply() public {
        assertEq(nft.totalSupply(), 0);
        nft.mint(user);
        assertEq(nft.totalSupply(), 1);
        nft.mint(user);
        assertEq(nft.totalSupply(), 2);
    }
}
