// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Token} from "../src/Token.sol";

contract TokenTest is Test {
    Token public token;
    address public admin;
    address public minter;
    address public user;

    function setUp() public {
        admin = address(this);
        minter = makeAddr("minter");
        user = makeAddr("user");

        token = new Token("{{TOKEN_NAME}}", "{{TOKEN_SYMBOL}}");
    }

    function test_Name() public view {
        assertEq(token.name(), "{{TOKEN_NAME}}");
    }

    function test_Symbol() public view {
        assertEq(token.symbol(), "{{TOKEN_SYMBOL}}");
    }

    function test_AdminHasMinterRole() public view {
        assertTrue(token.hasRole(token.MINTER_ROLE(), admin));
    }

    function test_AdminHasAdminRole() public view {
        assertTrue(token.hasRole(token.DEFAULT_ADMIN_ROLE(), admin));
    }

    function test_MinterCanMint() public {
        uint256 amount = 1000 ether;
        token.mint(user, amount);
        assertEq(token.balanceOf(user), amount);
    }

    function test_GrantMinterRole() public {
        token.grantRole(token.MINTER_ROLE(), minter);
        assertTrue(token.hasRole(token.MINTER_ROLE(), minter));

        vm.prank(minter);
        token.mint(user, 500 ether);
        assertEq(token.balanceOf(user), 500 ether);
    }

    function test_RevertWhen_NonMinterMints() public {
        vm.prank(user);
        vm.expectRevert();
        token.mint(user, 100 ether);
    }

    function test_RevokeMinterRole() public {
        token.grantRole(token.MINTER_ROLE(), minter);
        token.revokeRole(token.MINTER_ROLE(), minter);
        assertFalse(token.hasRole(token.MINTER_ROLE(), minter));
    }

    function test_Transfer() public {
        uint256 amount = 1000 ether;
        token.mint(admin, amount);

        token.transfer(user, 100 ether);
        assertEq(token.balanceOf(user), 100 ether);
        assertEq(token.balanceOf(admin), 900 ether);
    }

    function test_Approve_And_TransferFrom() public {
        uint256 amount = 1000 ether;
        token.mint(admin, amount);

        token.approve(minter, 500 ether);
        assertEq(token.allowance(admin, minter), 500 ether);

        vm.prank(minter);
        token.transferFrom(admin, user, 200 ether);
        assertEq(token.balanceOf(user), 200 ether);
        assertEq(token.allowance(admin, minter), 300 ether);
    }
}
