# Threat Model

## Assets

1. **User Deposits**: ETH held for each user
2. **Total Vault Balance**: All ETH in the contract
3. **Operational Status**: Ability to deposit/withdraw

## Threat Actors

| Actor | Capability | Motivation |
|-------|------------|------------|
| External attacker | Contract interaction | Steal funds, DoS |
| Compromised pauser | Pause control | Freeze funds, extort |
| Compromised admin | Role management | Grant malicious pauser |
| Malicious user | Deposit/withdraw | Exploit vulnerabilities |

## Threats and Mitigations

### T1: Reentrancy Attack

**Threat**: Attacker reenters during withdrawal

**Mitigation**: ReentrancyGuard on withdraw functions

**Residual Risk**: None with proper implementation

### T2: Pauser Abuse

**Threat**: Pauser freezes funds indefinitely

**Mitigation**: None in contract (trust model)

**Recommendation**: Use multi-sig, add time-limited pause

### T3: Admin Key Compromise

**Threat**: Attacker gains admin role

**Mitigation**: Access control limits damage

**Recommendation**: Use multi-sig for admin

### T4: Balance Manipulation

**Threat**: Attacker withdraws more than deposited

**Mitigation**: Balance tracking, checked math

**Residual Risk**: None with Solidity 0.8+

### T5: DoS via Pause

**Threat**: Attacker becomes pauser and pauses forever

**Mitigation**: Role management by admin

**Recommendation**: Add pause timeout, use multi-sig

### T6: Front-Running Withdrawals

**Threat**: Attacker frontruns large withdrawals

**Mitigation**: Not applicable (user withdraws own funds)

**Residual Risk**: None

## Trust Assumptions

1. Admin role holder is trustworthy
2. Pauser role holders are trustworthy
3. OpenZeppelin contracts are secure
4. Ethereum network is functioning normally

## Recommendations

1. Transfer admin to multi-sig after deployment
2. Use multi-sig or DAO for pauser role
3. Add maximum pause duration
4. Consider withdrawal time-locks for large amounts
5. Add monitoring for unusual activity
6. Consider insurance or reserves for user protection
