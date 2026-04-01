# Querit Search Plugin for Claude Code

A Claude Code plugin that integrates Querit.ai's powerful search API, enabling Claude to access real-time web information, technical documentation, and current events.

## Features

- 🔍 **Real-time Web Search**: Access up-to-date information beyond Claude's knowledge cutoff
- 🎯 **Smart Filtering**: Filter by date, language, country, and specific websites
- 📚 **Comprehensive Results**: Get titles, URLs, snippets, and source information
- 🚀 **Easy Integration**: Simple setup with environment variable configuration
- 🤖 **Proactive Usage**: Claude automatically uses search when needed

## Installation

### Prerequisites

- Claude Code CLI (version 1.0.33 or higher)
- A Querit.ai API key (get yours at [https://querit.ai](https://querit.ai))

### Method 1: Add Marketplace from GitHub

The easiest way to install and get automatic updates:

```bash
claude
# In Claude, add the marketplace:
/plugin marketplace add github:querit-ai/claude-querit

# Then install the plugin:
/plugin install querit-search@querit-marketplace
```

### Method 2: Add Marketplace from Git URL

#### Using HTTPS:
```bash
/plugin marketplace add https://github.com/querit-ai/claude-querit.git
/plugin install querit-search@querit-marketplace
```

#### Using SSH:
```bash
/plugin marketplace add git@github.com:querit-ai/claude-querit.git
/plugin install querit-search@querit-marketplace
```

#### Add Specific Branch or Tag:
```bash
# Add a specific version/tag
/plugin marketplace add https://github.com/querit-ai/claude-querit.git#v1.0.0

# Add a specific branch
/plugin marketplace add https://github.com/querit-ai/claude-querit.git#main
```

### Method 3: Add from Other Git Hosts

Works with any Git hosting service (GitLab, Bitbucket, self-hosted):

```bash
# GitLab example
/plugin marketplace add https://gitlab.com/your-org/claude-querit.git

# Bitbucket example
/plugin marketplace add https://bitbucket.org/your-org/claude-querit.git

# Self-hosted Git server
/plugin marketplace add https://git.yourcompany.com/plugins/claude-querit.git
```

### Method 4: Add from Local Path

First, get the plugin files locally:

**Option A: Clone the repository**
```bash
git clone https://github.com/querit-ai/claude-querit.git
cd claude-querit
```

**Option B: Download release**
```bash
# Download from GitHub releases
curl -L https://github.com/querit-ai/claude-querit/archive/refs/tags/v1.0.0.tar.gz -o claude-querit.tar.gz
tar -xzf claude-querit.tar.gz
cd claude-querit-1.0.0
```

Or manually download from: https://github.com/querit-ai/claude-querit/releases

#### From Local Directory:
```bash
# Add marketplace from local directory containing .claude-plugin/marketplace.json
/plugin marketplace add ./claude-querit

# Then install
/plugin install querit-search@querit-marketplace
```

#### From Direct marketplace.json Path:
```bash
/plugin marketplace add ./path/to/claude-querit/.claude-plugin/marketplace.json
/plugin install querit-search@querit-marketplace
```

### Method 5: Direct Load (Development/Testing)

Load the plugin directly without adding to marketplace:

```bash
# Clone the repository
git clone https://github.com/querit-ai/claude-querit.git

# Load directly with --plugin-dir flag
claude --plugin-dir ./claude-querit
```

### Method 6: Install from Official Marketplace

Once published to the official Claude Code plugins marketplace:

```bash
claude
# In Claude:
/plugin install querit-search@claude-plugins-official
```

## Configuration

When you first use the search feature, Claude will prompt you for your Querit.ai API key.

**Get your API key**: Visit [https://querit.ai](https://querit.ai) to sign up and obtain your API key.

The API key will be remembered for the duration of your conversation session. You'll need to provide it again in a new session.

## Usage

Once installed, Claude will automatically use the Querit search when appropriate. You can also explicitly request searches:

### Basic Search

```
Search for the latest React 19 features
```

### Recent Information

```
Find articles about AI developments from the past week
```

### Technical Documentation

```
Look up Stripe API documentation for subscription billing
```

### Specific Queries

```
Search for Python performance optimization techniques
```

## How It Works

The plugin provides a skill that:

1. **Triggers automatically** when Claude needs current information
2. **Calls the Querit.ai API** with your search query
3. **Formats results** with titles, URLs, snippets, and relevance
4. **Synthesizes information** to answer your questions

## Advanced Features

### Time-based Filtering

```
Find news about SpaceX from the last 30 days
```

### Language-specific Search

```
Search for German documentation about Vue.js
```

### Site-specific Search

```
Search GitHub and Stack Overflow for Redis examples
```

## API Details

The plugin uses the Querit.ai Search API v1:

- **Endpoint**: `https://api.querit.ai/v1/search`
- **Authentication**: Bearer token
- **Rate Limits**: Based on your Querit.ai plan

### Available Filters

- **Time Range**: Last N days/weeks/months/years, or specific date ranges
- **Languages**: English, Japanese, Korean, German, French, Spanish, Portuguese
- **Countries**: Argentina, Australia, Brazil, Canada, Colombia, France, Germany, India, Indonesia, Japan, Mexico, Nigeria, Philippines, South Korea, Spain, United Kingdom, United States
- **Sites**: Include or exclude specific domains

## Testing

Run the included test cases:

```bash
# Load plugin with test directory
claude --plugin-dir .

# Run test prompts from evals/evals.json
```

## Development

### Project Structure

```
claude-querit/
├── .claude-plugin/
│   └── plugin.json           # Plugin metadata
├── skills/
│   └── querit-search/
│       └── SKILL.md          # Main skill definition
├── evals/
│   └── evals.json            # Test cases
├── README.md                 # This file
└── LICENSE                   # License information
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `claude --plugin-dir .`
5. Submit a pull request

## Troubleshooting

### "401 Unauthorized" Error

- Your API key is invalid or expired
- Get a valid API key at [https://querit.ai](https://querit.ai)
- Claude will prompt you for a new key when needed

### "429 Too Many Requests" Error

- You've hit the rate limit for your API plan
- Wait a few moments and try again
- Consider upgrading your Querit.ai plan for higher limits

### Plugin Not Loading

- Ensure Claude Code version is 1.0.33 or higher: `claude --version`
- Check plugin structure matches the expected format
- Run `/reload-plugins` to reload without restarting

### Search Not Triggering

- Explicitly mention "search" or "find" in your query
- Make sure the plugin is installed: `/help` should show `/querit-search:querit-search`

## License

[Your chosen license - MIT recommended for open source]

## Links

- **Querit.ai**: [https://querit.ai](https://querit.ai)
- **API Documentation**: [https://querit.ai/docs](https://querit.ai/docs)
- **Claude Code Documentation**: [https://code.claude.com](https://code.claude.com)
- **Report Issues**: [GitHub Issues](https://github.com/querit-ai/claude-querit/issues)

## Credits

Created for the Claude Code community. Powered by [Querit.ai](https://querit.ai).

---

**Note**: This plugin requires a valid Querit.ai API key. Visit [https://querit.ai](https://querit.ai) to sign up and get your API key.
