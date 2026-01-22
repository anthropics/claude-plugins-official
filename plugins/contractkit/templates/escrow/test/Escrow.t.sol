// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {Escrow} from "../src/Escrow.sol";

contract EscrowTest is Test {
    Escrow public escrow;
    address public payer;
    address public payee;
    address public arbiter;
    uint256 public constant AMOUNT = 1 ether;

    function setUp() public {
        payer = makeAddr("payer");
        payee = makeAddr("payee");
        arbiter = makeAddr("arbiter");

        vm.deal(payer, 10 ether);

        vm.prank(payer);
        escrow = new Escrow(payee, arbiter, AMOUNT);
    }

    function test_InitialState() public view {
        assertEq(escrow.payer(), payer);
        assertEq(escrow.payee(), payee);
        assertEq(escrow.arbiter(), arbiter);
        assertEq(escrow.amount(), AMOUNT);
        assertEq(uint256(escrow.state()), uint256(Escrow.State.Created));
    }

    function test_Fund() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        assertEq(uint256(escrow.state()), uint256(Escrow.State.Funded));
        assertEq(escrow.balance(), AMOUNT);
    }

    function test_RevertWhen_FundWrongAmount() public {
        vm.prank(payer);
        vm.expectRevert(Escrow.InvalidAmount.selector);
        escrow.fund{value: 0.5 ether}();
    }

    function test_RevertWhen_NonPayerFunds() public {
        vm.prank(payee);
        vm.expectRevert(Escrow.Unauthorized.selector);
        escrow.fund{value: AMOUNT}();
    }

    function test_Release() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        uint256 payeeBalanceBefore = payee.balance;

        vm.prank(payer);
        escrow.release();

        assertEq(uint256(escrow.state()), uint256(Escrow.State.Released));
        assertEq(payee.balance, payeeBalanceBefore + AMOUNT);
        assertEq(escrow.balance(), 0);
    }

    function test_RevertWhen_NonPayerReleases() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        vm.prank(payee);
        vm.expectRevert(Escrow.Unauthorized.selector);
        escrow.release();
    }

    function test_Refund() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        uint256 payerBalanceBefore = payer.balance;

        vm.prank(payee);
        escrow.refund();

        assertEq(uint256(escrow.state()), uint256(Escrow.State.Refunded));
        assertEq(payer.balance, payerBalanceBefore + AMOUNT);
        assertEq(escrow.balance(), 0);
    }

    function test_RevertWhen_NonPayeeRefunds() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        vm.prank(payer);
        vm.expectRevert(Escrow.Unauthorized.selector);
        escrow.refund();
    }

    function test_Dispute() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        vm.prank(payer);
        escrow.dispute();

        assertEq(uint256(escrow.state()), uint256(Escrow.State.Disputed));
    }

    function test_PayeeCanDispute() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        vm.prank(payee);
        escrow.dispute();

        assertEq(uint256(escrow.state()), uint256(Escrow.State.Disputed));
    }

    function test_ResolveForPayee() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        vm.prank(payer);
        escrow.dispute();

        uint256 payeeBalanceBefore = payee.balance;

        vm.prank(arbiter);
        escrow.resolve(payee);

        assertEq(uint256(escrow.state()), uint256(Escrow.State.Released));
        assertEq(payee.balance, payeeBalanceBefore + AMOUNT);
    }

    function test_ResolveForPayer() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        vm.prank(payee);
        escrow.dispute();

        uint256 payerBalanceBefore = payer.balance;

        vm.prank(arbiter);
        escrow.resolve(payer);

        assertEq(uint256(escrow.state()), uint256(Escrow.State.Refunded));
        assertEq(payer.balance, payerBalanceBefore + AMOUNT);
    }

    function test_RevertWhen_NonArbiterResolves() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        vm.prank(payer);
        escrow.dispute();

        vm.prank(payer);
        vm.expectRevert(Escrow.Unauthorized.selector);
        escrow.resolve(payer);
    }

    function test_RevertWhen_ResolveToInvalidWinner() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        vm.prank(payer);
        escrow.dispute();

        vm.prank(arbiter);
        vm.expectRevert(Escrow.Unauthorized.selector);
        escrow.resolve(arbiter);
    }

    function test_RevertWhen_ReleaseNotFunded() public {
        vm.prank(payer);
        vm.expectRevert();
        escrow.release();
    }

    function test_RevertWhen_DoubleFund() public {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}();

        vm.prank(payer);
        vm.expectRevert();
        escrow.fund{value: AMOUNT}();
    }
}
