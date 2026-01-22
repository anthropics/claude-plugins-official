// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Vault} from "../src/Vault.sol";

contract VaultTest is Test {
    Vault public vault;
    address public admin;
    address public user1;
    address public user2;

    function setUp() public {
        admin = address(this);
        user1 = makeAddr("user1");
        user2 = makeAddr("user2");

        vm.deal(user1, 10 ether);
        vm.deal(user2, 10 ether);

        vault = new Vault();
    }

    function test_AdminHasRoles() public view {
        assertTrue(vault.hasRole(vault.DEFAULT_ADMIN_ROLE(), admin));
        assertTrue(vault.hasRole(vault.PAUSER_ROLE(), admin));
    }

    function test_Deposit() public {
        vm.prank(user1);
        vault.deposit{value: 1 ether}();

        assertEq(vault.balanceOf(user1), 1 ether);
        assertEq(vault.totalDeposits(), 1 ether);
        assertEq(vault.vaultBalance(), 1 ether);
    }

    function test_MultipleDeposits() public {
        vm.prank(user1);
        vault.deposit{value: 1 ether}();

        vm.prank(user1);
        vault.deposit{value: 2 ether}();

        assertEq(vault.balanceOf(user1), 3 ether);
    }

    function test_RevertWhen_DepositZero() public {
        vm.prank(user1);
        vm.expectRevert(Vault.ZeroAmount.selector);
        vault.deposit{value: 0}();
    }

    function test_Withdraw() public {
        vm.prank(user1);
        vault.deposit{value: 2 ether}();

        uint256 balanceBefore = user1.balance;

        vm.prank(user1);
        vault.withdraw(1 ether);

        assertEq(vault.balanceOf(user1), 1 ether);
        assertEq(user1.balance, balanceBefore + 1 ether);
    }

    function test_WithdrawAll() public {
        vm.prank(user1);
        vault.deposit{value: 3 ether}();

        uint256 balanceBefore = user1.balance;

        vm.prank(user1);
        vault.withdrawAll();

        assertEq(vault.balanceOf(user1), 0);
        assertEq(user1.balance, balanceBefore + 3 ether);
    }

    function test_RevertWhen_WithdrawMoreThanBalance() public {
        vm.prank(user1);
        vault.deposit{value: 1 ether}();

        vm.prank(user1);
        vm.expectRevert(
            abi.encodeWithSelector(Vault.InsufficientBalance.selector, 2 ether, 1 ether)
        );
        vault.withdraw(2 ether);
    }

    function test_RevertWhen_WithdrawZero() public {
        vm.prank(user1);
        vm.expectRevert(Vault.ZeroAmount.selector);
        vault.withdraw(0);
    }

    function test_RevertWhen_WithdrawAllWithZeroBalance() public {
        vm.prank(user1);
        vm.expectRevert(Vault.ZeroAmount.selector);
        vault.withdrawAll();
    }

    function test_MultipleUsers() public {
        vm.prank(user1);
        vault.deposit{value: 1 ether}();

        vm.prank(user2);
        vault.deposit{value: 2 ether}();

        assertEq(vault.balanceOf(user1), 1 ether);
        assertEq(vault.balanceOf(user2), 2 ether);
        assertEq(vault.totalDeposits(), 3 ether);
    }

    function test_Pause() public {
        vault.pause();
        assertTrue(vault.paused());
    }

    function test_Unpause() public {
        vault.pause();
        vault.unpause();
        assertFalse(vault.paused());
    }

    function test_RevertWhen_DepositWhilePaused() public {
        vault.pause();

        vm.prank(user1);
        vm.expectRevert(Vault.ContractPaused.selector);
        vault.deposit{value: 1 ether}();
    }

    function test_RevertWhen_WithdrawWhilePaused() public {
        vm.prank(user1);
        vault.deposit{value: 1 ether}();

        vault.pause();

        vm.prank(user1);
        vm.expectRevert(Vault.ContractPaused.selector);
        vault.withdraw(1 ether);
    }

    function test_RevertWhen_NonPauserPauses() public {
        vm.prank(user1);
        vm.expectRevert();
        vault.pause();
    }

    function test_GrantPauserRole() public {
        vault.grantRole(vault.PAUSER_ROLE(), user1);

        vm.prank(user1);
        vault.pause();
        assertTrue(vault.paused());
    }

    function test_TotalDepositsTracking() public {
        vm.prank(user1);
        vault.deposit{value: 2 ether}();

        vm.prank(user2);
        vault.deposit{value: 3 ether}();

        assertEq(vault.totalDeposits(), 5 ether);

        vm.prank(user1);
        vault.withdraw(1 ether);

        assertEq(vault.totalDeposits(), 4 ether);
    }
}
