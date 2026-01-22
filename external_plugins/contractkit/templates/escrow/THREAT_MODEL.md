# Threat Model

## Assets

1. **Escrowed Funds**: ETH held in the contract
2. **Agreement Terms**: Payer, payee, arbiter, amount
3. **State Integrity**: Correct state transitions

## Threat Actors

| Actor | Capability | Motivation |
|-------|------------|------------|
| Malicious payer | Fund/release/dispute | Refuse to release, false dispute |
| Malicious payee | Refund/dispute | Refuse service, false dispute |
| Malicious arbiter | Resolve disputes | Collude with party, extort |
| External attacker | Contract interaction | Steal funds, manipulate state |

## Threats and Mitigations

### T1: Reentrancy Attack

**Threat**: Attacker reenters during fund transfer

**Mitigation**: ReentrancyGuard on all fund-transferring functions

**Residual Risk**: None with proper implementation

### T2: Arbiter Collusion

**Threat**: Arbiter colludes with payer or payee

**Mitigation**: None in contract (trust model)

**Recommendation**: Use reputable arbitration service, multi-sig arbiter

### T3: Denial by Payer

**Threat**: Payer never releases after receiving service

**Mitigation**: Payee can dispute, arbiter resolves

**Recommendation**: Add time-based auto-release

### T4: Denial by Payee

**Threat**: Payee never delivers after receiving funds

**Mitigation**: Payer can dispute, arbiter resolves

**Recommendation**: Add time-based auto-refund

### T5: Griefing via Dispute

**Threat**: Party disputes to delay resolution

**Mitigation**: Arbiter can resolve quickly

**Recommendation**: Add dispute bond/fee

### T6: Front-Running

**Threat**: Attacker frontruns state changes

**Mitigation**: State changes are permissioned

**Residual Risk**: Low, attacker gains nothing

## Trust Assumptions

1. Arbiter is honest and competent
2. At least one of payer/payee is honest
3. OpenZeppelin ReentrancyGuard is secure
4. Ethereum network is functioning normally

## Recommendations

1. Use multi-sig or DAO as arbiter
2. Add time limits for each state
3. Consider adding dispute bonds
4. Document off-chain dispute process
5. Consider adding partial release capability
6. Add event monitoring for suspicious activity
