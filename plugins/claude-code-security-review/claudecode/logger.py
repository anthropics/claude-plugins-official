"""Logging configuration for ClaudeCode."""

import logging
import sys
import os


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger that outputs to stderr.
    
    Args:
        name: The name of the logger (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        
        # Get repo and PR number from environment for prefix
        repo_name = os.environ.get('GITHUB_REPOSITORY', '')
        pr_number = os.environ.get('PR_NUMBER', '')
        
        # Build prefix
        if repo_name and pr_number:
            prefix = f"[{repo_name}#{pr_number}]"
        elif repo_name:
            prefix = f"[{repo_name}]"
        elif pr_number:
            prefix = f"[PR#{pr_number}]"
        else:
            prefix = ""
        
        # Include prefix in format if available
        if prefix:
            format_str = f'{prefix} [%(name)s] %(message)s'
        else:
            format_str = '[%(name)s] %(message)s'
        
        formatter = logging.Formatter(format_str)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger