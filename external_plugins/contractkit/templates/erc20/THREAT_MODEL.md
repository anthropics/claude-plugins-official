# Threat Model

## Assets

1. **Token Supply**: Total tokens in circulation
2. **User Balances**: Individual token holdings
3. **Admin Access**: Control over role assignments
4. **Minter Access**: Ability to create new tokens

## Threat Actors

| Actor | Capability | Motivation |
|-------|------------|------------|
| External attacker | Contract interaction | Steal tokens, manipulate supply |
| Compromised minter | Mint function access | Infinite mint attack |
| Compromised admin | Role management | Grant malicious minter |
| Malicious deployer | Initial role holder | Rug pull via minting |

## Threats and Mitigations

### T1: Unauthorized Minting

**Threat**: Attacker calls mint without permission

**Mitigation**: AccessControl enforces MINTER_ROLE check

**Residual Risk**: None if role not granted

### T2: Admin Key Compromise

**Threat**: Attacker gains admin private key

**Mitigation**: None in contract (operational security)

**Recommendation**: Use multi-sig wallet for admin

### T3: Minter Key Compromise

**Threat**: Attacker gains minter private key

**Mitigation**: Admin can revoke minter role

**Recommendation**: Monitor minting events, use time-locked minting

### T4: Unlimited Supply Inflation

**Threat**: Malicious minter creates unlimited tokens

**Mitigation**: None in this template

**Recommendation**: Add supply cap if needed

## Trust Assumptions

1. Admin role holder is trustworthy
2. Minter role holders are trustworthy
3. OpenZeppelin contracts are secure
4. Solidity compiler is not compromised

## Recommendations

1. Transfer admin to multi-sig after deployment
2. Implement minting limits or caps
3. Add monitoring for large mints
4. Consider time-locks for sensitive operations
