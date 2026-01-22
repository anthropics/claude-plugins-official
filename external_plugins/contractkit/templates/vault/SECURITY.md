# Security

## Status

**NOT AUDITED** - This contract is a template for development purposes.

## Dependencies

- OpenZeppelin ReentrancyGuard (audited)
- OpenZeppelin AccessControl (audited)

## Known Considerations

1. **Pauser Trust**: PAUSER_ROLE can freeze user funds indefinitely.
2. **ETH Only**: Does not support ERC20 tokens.
3. **No Yield**: Funds sit idle; no interest or rewards.
4. **No Withdrawal Limits**: Users can withdraw any amount up to their balance.
5. **Reentrancy**: Protected by ReentrancyGuard.

## Before Mainnet

- [ ] Get independent security audit
- [ ] Set up multi-sig for admin and pauser roles
- [ ] Consider time-locked pause mechanism
- [ ] Review all role assignments
- [ ] Test pause/unpause edge cases
- [ ] Consider withdrawal limits or time-locks
