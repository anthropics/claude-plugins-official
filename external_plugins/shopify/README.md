# Shopify Dev MCP Plugin

Connect Claude Code to Shopify's development resources. This plugin enables Claude to search Shopify docs, explore API schemas, build Functions, and provide accurate guidance based on current Shopify APIs and best practices.

## Tools Provided

- **learn_shopify_api** - Start here. Teaches Claude about supported Shopify APIs and how to use the MCP server's tools
- **search_docs_chunks** - Search across all shopify.dev documentation
- **fetch_full_docs** - Retrieve complete documentation for specific paths
- **introspect_graphql_schema** - Explore Shopify GraphQL schemas (Admin, Storefront, Partner, Customer, Payments Apps, Functions)
- **validate_graphql_codeblocks** - Validate GraphQL code against Shopify schemas
- **validate_component_codeblocks** - Validate Polaris and UI extension components
- **validate_theme** - Validate Liquid theme directories

## Supported APIs

- Admin GraphQL API
- Liquid and theme development
- Storefront GraphQL API
- Partner API
- Customer Account API
- Payments Apps API
- Shopify Functions (Discounts, Cart Transform, Delivery Customization, etc.)
- Polaris (App Home, Admin Extensions, Checkout Extensions, Customer Account Extensions, Point of Sale Extensions)


## Links

- [Documentation](https://shopify.dev/docs/apps/build/devmcp)
- [npm Package](https://www.npmjs.com/package/@shopify/dev-mcp)
