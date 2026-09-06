#!/usr/bin/env python3
"""UserPromptSubmit hook executor for hookify plugin.

This script is called by Claude Code when user submits a prompt.
It reads .claude/hookify.*.local.md files and evaluates rules.
"""

import os
import sys
import json

# Add plugin root to Python path for imports
PLUGIN_ROOT = os.environ.get('CLAUDE_PLUGIN_ROOT')
if PLUGIN_ROOT and PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

try:
    from core.config_loader import load_rules
    from core.rule_engine import RuleEngine
except ImportError as e:
    error_msg = {"systemMessage": f"Hookify import error: {e}"}
    print(json.dumps(error_msg), file=sys.stdout)
    sys.exit(0)


def main():
    """Main entry point for UserPromptSubmit hook."""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)

        # Load user prompt rules
        rules = load_rules(event='prompt')

        # Evaluate rules
        engine = RuleEngine()
        result = engine.evaluate_rules(rules, input_data)

        # Always output JSON (even if empty)
        print(json.dumps(result), file=sys.stdout)

    except json.JSONDecodeError as e:
        # The payload could not be parsed, so there is nothing to evaluate.
        # Windows file paths arrive with raw backslashes, and sequences like
        # \U or \D are not valid JSON escapes, so this fires on ordinary tool
        # calls. Reporting it through systemMessage put an error in front of
        # the user on every single call for something they cannot act on, so
        # it goes to stderr for diagnosis instead.
        print(f"Hookify could not parse hook input: {e}", file=sys.stderr)

    except Exception as e:
        error_output = {
            "systemMessage": f"Hookify error: {str(e)}"
        }
        print(json.dumps(error_output), file=sys.stdout)

    finally:
        # ALWAYS exit 0
        sys.exit(0)


if __name__ == '__main__':
    main()
