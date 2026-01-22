# Threat Model

## Assets

1. **NFT Ownership**: Who owns each token
2. **Collection Supply**: Total tokens in existence
3. **Admin Access**: Control over role assignments
4. **Minter Access**: Ability to create new NFTs
5. **Metadata Control**: Ability to change token URIs

## Threat Actors

| Actor | Capability | Motivation |
|-------|------------|------------|
| External attacker | Contract interaction | Steal NFTs, manipulate metadata |
| Compromised minter | Mint function access | Flood supply, devalue collection |
| Compromised admin | Role management + URI control | Grant malicious minter, rug via metadata |
| Malicious deployer | Initial role holder | Rug pull via minting or metadata change |

## Threats and Mitigations

### T1: Unauthorized Minting

**Threat**: Attacker mints without permission

**Mitigation**: AccessControl enforces MINTER_ROLE check

**Residual Risk**: None if role not granted

### T2: Admin Key Compromise

**Threat**: Attacker gains admin private key

**Mitigation**: None in contract (operational security)

**Recommendation**: Use multi-sig wallet for admin

### T3: Metadata Manipulation

**Threat**: Admin changes base URI to malicious content

**Mitigation**: None in contract

**Recommendation**: Consider time-lock for URI changes, or make URI immutable after launch

### T4: Unlimited Supply Dilution

**Threat**: Minter floods collection with new NFTs

**Mitigation**: None in this template

**Recommendation**: Add supply cap if collection size matters

### T5: Transfer Frontrunning

**Threat**: Attacker frontruns transfers or approvals

**Mitigation**: Standard ERC721 behavior

**Recommendation**: Use permit patterns or private mempools for high-value transfers

## Trust Assumptions

1. Admin role holder is trustworthy
2. Minter role holders are trustworthy
3. OpenZeppelin contracts are secure
4. Metadata hosting is reliable and secure

## Recommendations

1. Transfer admin to multi-sig after deployment
2. Implement minting limits or supply cap
3. Consider making base URI immutable after reveal
4. Add monitoring for minting activity
5. Consider ERC2981 royalties for secondary sales
