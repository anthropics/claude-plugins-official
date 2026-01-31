# ScrapeGraphAI Plugin

Intelligent web scraping service with LLM-powered content extraction, browser automation, and multi-site search capabilities.

## Overview

ScrapeGraphAI provides advanced web scraping capabilities including:

- **Smart Scraping**: LLM-powered content extraction from websites
- **Basic Scraping**: Simple HTML retrieval without LLM processing
- **Search Scraping**: Multi-site scraping from search results
- **Browser Automation**: Agentic scraping with browser interaction and workflows
- **Website Crawling**: Intelligent crawling with AI extraction (Smart Crawler and Crawl Job)
- **Markdown Conversion**: Clean HTML to Markdown conversion
- **Scheduled Jobs**: Automated recurring scraping tasks with cron scheduling
- **Schema Generation**: Generate JSON schemas from natural language
- **Sitemap Extraction**: Discover and extract all URLs from websites
- **Data Transformation**: Toonify format conversion
- **Session Management**: Live browser sessions and workflow execution

## Setup

### API Key Configuration

1. Get your API key from [ScrapeGraphAI](https://scrapegraphai.com)
2. Set the environment variable:
   ```bash
   export SCRAPEGRAPHAI_API_KEY=your-api-key-here
   ```

The plugin will automatically use this API key for all requests.

## API Endpoints

### Smart Scraper (`/smartscraper`)

Main scraping endpoint with LLM-powered content analysis. Supports:
- URL-based scraping
- Local HTML/Markdown processing
- Custom output schemas
- Infinite scrolling and pagination
- Stealth mode for bot detection avoidance

**Example Request:**
```json
{
  "user_prompt": "Extract product name, price, and description",
  "website_url": "https://example.com/product",
  "output_schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "price": {"type": "number"},
      "description": {"type": "string"}
    }
  }
}
```

### Search Scraper (`/searchscraper`)

Search and scrape multiple websites with three modes:
- **AI Extraction Mode**: LLM-powered structured data extraction
- **Markdown Conversion Mode**: Convert pages to markdown
- **Raw Mode**: Return search results as-is

**Example Request:**
```json
{
  "user_prompt": "Find the latest AI news and extract headlines and summaries",
  "num_results": 5,
  "extraction_mode": true
}
```

### Agentic Scrapper (`/agentic-scrapper`)

Advanced browser automation with:
- Custom interaction steps
- Session management
- AI-powered extraction
- Multi-step workflows

**Example Request:**
```json
{
  "url": "https://example.com",
  "user_prompt": "Extract all product listings",
  "steps": ["Click the 'Load More' button", "Wait for products to load"],
  "ai_extraction": true
}
```

### Smart Crawler (`/smartcrawler`)

Intelligent website crawling with:
- AI extraction or markdown conversion
- Custom queries
- Batch processing
- Session management

**Example Request:**
```json
{
  "website_url": "https://example.com",
  "input_queries": ["What products are available?", "What are the prices?"],
  "extraction_mode": true
}
```

### Markdownify (`/markdownify`)

Convert web pages to clean Markdown format.

**Example Request:**
```json
{
  "website_url": "https://example.com/article"
}
```

### Basic Scrape (`/scrape`)

Simple HTML scraping without LLM processing.

**Example Request:**
```json
{
  "website_url": "https://example.com",
  "render_heavy_js": true
}
```

### Sitemap (`/sitemap`)

Extract all URLs from a website's sitemap.

**Example Request:**
```json
{
  "website_url": "https://example.com"
}
```

### Schema Generator (`/generate_schema`)

Generate JSON schemas from natural language descriptions.

**Example Request:**
```json
{
  "user_prompt": "Create a schema for product information including name, price, and reviews"
}
```

### Crawl Job (`/crawl`)

Comprehensive website crawling with sitemap support. Supports both AI extraction mode and markdown conversion mode.

**Example Request:**
```json
{
  "url": "https://example.com",
  "depth": 2,
  "max_pages": 50,
  "extraction_mode": true,
  "prompt": "Extract all product information",
  "sitemap": true
}
```

### Workflow Execution (`/run-workflow`)

Execute multi-step agentic browser workflows with navigation, actions, extractions, loops, and conditionals.

**Example Request:**
```json
{
  "name": "Product Scraper",
  "start_url": "https://shop.example.com",
  "use_session": true,
  "steps": [
    {"type": "navigate", "url": "https://shop.example.com/products"},
    {"type": "action", "action": "Click 'Load More' button"},
    {"type": "extract", "instruction": "Extract all products", "save_to": "products"}
  ],
  "initial_context": {},
  "output_variables": ["products"]
}
```

### Agentic Scrapper Session Management

- `POST /get-live-session-url` - Get live session URL for browser interaction
- `POST /stop-session` - Stop an active browser session

**Example:**
```json
{
  "url": "https://example.com",
  "timeout": 300
}
```

### Scheduled Jobs (`/scheduled-jobs`)

Create, manage, and monitor automated recurring scraping jobs:

- `POST /scheduled-jobs` - Create a new scheduled job
- `GET /scheduled-jobs` - List all scheduled jobs (with filters: status, service_type, is_active)
- `GET /scheduled-jobs/{job_id}` - Get job details
- `PUT /scheduled-jobs/{job_id}` - Update job
- `DELETE /scheduled-jobs/{job_id}` - Delete job
- `POST /scheduled-jobs/{job_id}/pause` - Pause job
- `POST /scheduled-jobs/{job_id}/resume` - Resume job
- `POST /scheduled-jobs/{job_id}/trigger` - Trigger job manually
- `GET /scheduled-jobs/{job_id}/executions` - Get job execution history

**Service Types Supported:**
- `smartscraper`
- `searchscraper`
- `markdownify`
- `smartcrawler`
- `agenticscrapper`

**Example Create Job:**
```json
{
  "job_name": "Daily News Scrape",
  "service_type": "smartscraper",
  "cron_expression": "0 9 * * *",
  "job_config": {
    "user_prompt": "Extract headlines and summaries",
    "website_url": "https://news.example.com"
  },
  "webhook_url": "https://your-webhook.com/results"
}
```

### Toonify (`/toonify`)

Convert data objects to toon format.

**Example Request:**
```json
{
  "products": [
    {"sku": "LAP-001", "name": "Gaming Laptop", "price": 1299.99},
    {"sku": "MOU-042", "name": "Wireless Mouse", "price": 29.99}
  ]
}
```

### User Management

- `GET /credits` - Get credit balance and usage
- `GET /validate` - Validate API key and get associated email

### Feedback

- `POST /feedback` - Submit feedback for a specific request
- `POST /product-feedback` - Submit general product feedback (no auth required)

**Example Feedback:**
```json
{
  "request_id": "uuid",
  "rating": 5,
  "feedback_text": "Great results!"
}
```

### Health Check

- `GET /healthz` - Check service health status (no auth required)

## Authentication

All API requests require authentication via the `SGAI-APIKEY` header:

```
SGAI-APIKEY: your-api-key-here
```

## Credit System

ScrapeGraphAI uses a credit-based system:
- Check credits: `GET /credits`
- Different endpoints consume different credit amounts:
  - Smart scraper: 10 credits per page
  - Search scraper: 10 credits per website (AI mode) or 2 credits (markdown mode)
  - Markdown conversion: 2 credits per page
  - Basic scrape: 1 credit per page
  - Agentic scrapper: Variable based on complexity
  - Smart crawler: Variable based on pages crawled
  - Schema generation: Variable based on complexity

## Response Formats

### Async Operations

Many endpoints return a `request_id` or `session_id` for async operations. Check status with:

- `GET /smartscraper/{request_id}` - Check smart scraper status
- `GET /markdownify/{request_id}` - Check markdown conversion status
- `GET /searchscraper/{request_id}` - Check search scraper status
- `GET /smartcrawler/{session_id}` - Check smart crawler session status
- `GET /smartcrawler/sessions/all` - Get all smart crawler sessions
- `GET /generate_schema/{request_id}` - Check schema generation status
- `GET /crawl/{task_id}` - Check crawl job status

### Status Values

- `queued` - Request is queued for processing
- `processing` - Request is being processed
- `completed` - Request completed successfully
- `failed` - Request failed (check `error` field)

## Error Handling

Common error responses:

- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid API key)
- `402` - Insufficient Credits
- `404` - Not Found (request/session not found)
- `422` - Validation Error
- `500` - Internal Server Error

## Best Practices

1. **Use output schemas**: Define JSON schemas for consistent structured data
2. **Enable stealth mode**: For sites with bot detection (`stealth: true`)
3. **Use render_heavy_js**: For Single Page Applications and dynamic content
4. **Monitor credits**: Check credit balance before large operations
5. **Handle async operations**: Use request IDs to check status for long-running tasks
6. **Use scheduled jobs**: For recurring scraping tasks instead of manual calls

## Examples

### Extract Product Information

```bash
curl -X POST https://api.scrapegraphai.com/v1/smartscraper \
  -H "SGAI-APIKEY: $SCRAPEGRAPHAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "Extract product name, price, description, and availability",
    "website_url": "https://example.com/product/123",
    "output_schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "price": {"type": "number"},
        "description": {"type": "string"},
        "available": {"type": "boolean"}
      }
    }
  }'
```

### Search and Extract News

```bash
curl -X POST https://api.scrapegraphai.com/v1/searchscraper \
  -H "SGAI-APIKEY: $SCRAPEGRAPHAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "Find latest AI research papers and extract title, authors, and abstract",
    "num_results": 10,
    "extraction_mode": true
  }'
```

### Crawl Website with Queries

```bash
curl -X POST https://api.scrapegraphai.com/v1/smartcrawler \
  -H "SGAI-APIKEY: $SCRAPEGRAPHAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "website_url": "https://docs.example.com",
    "input_queries": [
      "What are the main API endpoints?",
      "What authentication methods are supported?"
    ],
    "extraction_mode": true
  }'
```

### Execute Browser Workflow

```bash
curl -X POST https://api.scrapegraphai.com/v1/run-workflow \
  -H "SGAI-APIKEY: $SCRAPEGRAPHAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product Scraper",
    "start_url": "https://shop.example.com",
    "steps": [
      {"type": "navigate", "url": "https://shop.example.com/products"},
      {"type": "extract", "instruction": "Extract all products", "save_to": "products"}
    ],
    "initial_context": {},
    "output_variables": ["products"]
  }'
```

### Create Scheduled Job

```bash
curl -X POST https://api.scrapegraphai.com/v1/scheduled-jobs \
  -H "SGAI-APIKEY: $SCRAPEGRAPHAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "Daily News Scrape",
    "service_type": "smartscraper",
    "cron_expression": "0 9 * * *",
    "job_config": {
      "user_prompt": "Extract headlines and summaries",
      "website_url": "https://news.example.com"
    }
  }'
```

### Generate Schema

```bash
curl -X POST https://api.scrapegraphai.com/v1/generate_schema \
  -H "SGAI-APIKEY: $SCRAPEGRAPHAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "Create a schema for product information including name, price, and reviews"
  }'
```

## Resources

- **API Documentation**: https://scrapegraphai.com/docs
- **Support**: https://scrapegraphai.com/support
- **API Base URL**: https://api.scrapegraphai.com/v1
- **Development Server**: http://localhost:8001/v1

## Version

Plugin version: 1.2.0 (matches API version)

