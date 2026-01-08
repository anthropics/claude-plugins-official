# Sugar - Autonomous Development for Claude Code

The dev team that never stops.

Sugar is an AI-powered autonomous development system that integrates with Claude Code for background task execution.

## Features

- **Autonomous Task Execution** - Let AI handle complex, multi-step development work
- **Task Queue Management** - Persistent SQLite-backed task tracking with rich metadata
- **Intelligent Agents** - Specialized agents for different development aspects
- **Work Discovery** - Finds work from error logs, GitHub issues, and code quality metrics
- **Dry Run Mode** - Test without making changes

## Installation

### Prerequisites

1. **Install Sugar CLI**:
   ```bash
   pip install sugar-ai
   ```

2. **Initialize in your project**:
   ```bash
   cd /path/to/your/project
   sugar init
   ```

### Plugin Installation

Install the Sugar plugin via Claude Code:
```
/install roboticforce/sugar
```

## Usage

### Create a Task
```
/sugar-add "Implement user authentication" --type feature --priority 2
```

### View Status
```
/sugar-status
```

### Start Autonomous Mode
```
/sugar-run --dry-run  # Test first
/sugar-run            # Start autonomous development
```

## Available Commands

- `/sugar-add` - Add tasks to the queue
- `/sugar-list` - List tasks with optional filtering
- `/sugar-status` - View system status and queue stats
- `/sugar-run` - Start autonomous execution (dry-run mode)
- `/sugar-view` - View detailed task information
- `/sugar-remove` - Remove tasks from the queue
- `/sugar-priority` - Change task priority

## Documentation

- [GitHub Repository](https://github.com/roboticforce/sugar)
- [PyPI Package](https://pypi.org/project/sugar-ai/)
- [Quick Start Guide](https://github.com/roboticforce/sugar/blob/main/docs/user/quick-start.md)
- [CLI Reference](https://github.com/roboticforce/sugar/blob/main/docs/user/cli-reference.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/roboticforce/sugar/issues)
- **Discussions**: [GitHub Discussions](https://github.com/roboticforce/sugar/discussions)

## License

MIT License - [LICENSE](https://github.com/roboticforce/sugar/blob/main/LICENSE)

## Author

Steven Leggett / [roboticforce](https://github.com/roboticforce)
