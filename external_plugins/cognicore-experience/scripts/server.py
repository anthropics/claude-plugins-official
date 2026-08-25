#!/usr/bin/env python
"""
CogniCore Structured Experience MCP Server for Claude Code.

Runs the stdio FastMCP server with the 5 experience tools:
- cognicore_record_experience
- cognicore_verify_experience
- cognicore_recall_experience
- cognicore_share_experience
- cognicore_check_experience
"""

import sys
import os
import logging
from pathlib import Path

# Ensure stderr logging so stdout is exclusively reserved for MCP JSON-RPC protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("cognicore-experience-mcp")

def main():
    try:
        from cognicore.integrations.claude_code import ClaudeCodeIntegration
    except ImportError as e:
        logger.error(
            "Failed to import cognicore. Please ensure cognicore-env[server,mcp] is installed: %s",
            e,
        )
        sys.exit(1)

    db_path = os.environ.get("COGNICORE_DB_PATH")
    if not db_path:
        default_dir = Path.home() / ".cognicore"
        default_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(default_dir / "experience_memory.db")
        os.environ["COGNICORE_DB_PATH"] = db_path

    logger.info("Starting CogniCore Experience MCP server with DB: %s", db_path)
    integration = ClaudeCodeIntegration(db_path=db_path)
    integration.run_stdio(name="cognicore-experience")

if __name__ == "__main__":
    main()
