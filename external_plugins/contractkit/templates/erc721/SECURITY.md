# Security

## Status

**NOT AUDITED** - This contract is a template for development purposes.

## Dependencies

- OpenZeppelin Contracts (audited)

## Known Considerations

1. **Admin Key Security**: The deployer receives DEFAULT_ADMIN_ROLE. Secure this key.
2. **Minter Trust**: MINTER_ROLE holders can mint unlimited NFTs.
3. **No Supply Cap**: There is no maximum supply limit by default.
4. **Base URI Control**: Admin can change metadata URI at any time.
5. **No Royalties**: This template does not include ERC2981 royalties.

## Before Mainnet

- [ ] Get independent security audit
- [ ] Set up multi-sig for admin role
- [ ] Consider supply caps if needed
- [ ] Review role assignments
- [ ] Set up proper metadata hosting
- [ ] Consider adding royalty support (ERC2981)
