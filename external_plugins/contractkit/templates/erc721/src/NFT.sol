// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @title {{TOKEN_NAME}}
/// @notice ERC721 NFT with role-based access control for minting
/// @dev Uses OpenZeppelin ERC721 and AccessControl
contract NFT is ERC721, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    uint256 private _nextTokenId;
    string private _baseTokenURI;

    /// @notice Creates a new NFT collection with the deployer as admin and minter
    /// @param name_ The collection name
    /// @param symbol_ The collection symbol
    /// @param baseURI_ The base URI for token metadata
    constructor(string memory name_, string memory symbol_, string memory baseURI_)
        ERC721(name_, symbol_)
    {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _baseTokenURI = baseURI_;
    }

    /// @notice Mints a new NFT to the specified address
    /// @dev Only callable by addresses with MINTER_ROLE
    /// @param to The address to mint the NFT to
    /// @return tokenId The ID of the newly minted token
    function mint(address to) external onlyRole(MINTER_ROLE) returns (uint256) {
        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
        return tokenId;
    }

    /// @notice Sets the base URI for token metadata
    /// @dev Only callable by addresses with DEFAULT_ADMIN_ROLE
    /// @param baseURI_ The new base URI
    function setBaseURI(string memory baseURI_) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _baseTokenURI = baseURI_;
    }

    /// @notice Returns the base URI for token metadata
    function _baseURI() internal view override returns (string memory) {
        return _baseTokenURI;
    }

    /// @notice Returns the total number of tokens minted
    function totalSupply() external view returns (uint256) {
        return _nextTokenId;
    }

    /// @dev Required override for AccessControl
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
