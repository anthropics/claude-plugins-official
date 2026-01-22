# Security

## Status

**NOT AUDITED** - This contract is a template for development purposes.

## Dependencies

- OpenZeppelin Contracts (audited)

## Known Considerations

1. **Admin Key Security**: The deployer receives DEFAULT_ADMIN_ROLE. Secure this key.
2. **Minter Trust**: MINTER_ROLE holders can mint unlimited tokens.
3. **No Supply Cap**: There is no maximum supply limit.
4. **No Pause**: This template does not include pause functionality.

## Before Mainnet

- [ ] Get independent security audit
- [ ] Set up multi-sig for admin role
- [ ] Consider supply caps if needed
- [ ] Review role assignments
- [ ] Test all access control paths
