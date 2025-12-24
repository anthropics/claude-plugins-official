#!/usr/bin/env python3
"""
YPM Project Scanning Script

Scans the monitored directories specified in ~/.ypm/config.yml,
collects Git information and documentation details from each project,
and outputs the results in JSON format.

Usage:
    python scripts/scan_projects.py
    python scripts/scan_projects.py --config /path/to/config.yml

Output:
    JSON format to standard output
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from datetime import datetime
import time
import glob
import argparse


def get_default_config_path():
    """Get the default configuration file path"""
    return Path.home() / ".ypm" / "config.yml"


def load_config(config_path=None):
    """Load config.yml"""
    if config_path is None:
        config_path = get_default_config_path()
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        print(json.dumps({
            "error": f"config.yml not found at {config_path}",
            "hint": "Run /ypm:setup to initialize YPM"
        }), file=sys.stderr)
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(json.dumps({"error": f"Failed to load config.yml: {e}"}), file=sys.stderr)
        sys.exit(1)


def find_projects(base_dirs, patterns, excludes):
    """
    Detect Git repositories based on patterns

    Args:
        base_dirs: List of monitored directories
        patterns: List of project detection patterns
        excludes: List of exclusion patterns

    Returns:
        List of project paths
    """
    projects = set()

    for base_dir in base_dirs:
        base_path = Path(base_dir).expanduser()

        if not base_path.exists():
            continue

        for pattern in patterns:
            # Search directories based on pattern
            search_pattern = str(base_path / pattern)

            for path in glob.glob(search_pattern):
                path_obj = Path(path)

                # Check if it's a directory and a Git repository
                if path_obj.is_dir() and (path_obj / ".git").exists():
                    # Convert to relative path
                    try:
                        rel_path = path_obj.relative_to(base_path)
                        rel_path_str = f"./{rel_path}"

                        # Check if it matches exclusion patterns
                        excluded = False
                        for exclude in excludes:
                            if exclude in rel_path_str:
                                excluded = True
                                break

                        if not excluded:
                            projects.add(str(path_obj))
                    except ValueError:
                        # Use absolute path if relative_to fails
                        projects.add(str(path_obj))

    return sorted(list(projects))


def run_git_command(project_path, command):
    """
    Execute a Git command in the specified project

    Args:
        project_path: Project path
        command: Git command (in list format)

    Returns:
        Command output (string), or None on failure
    """
    try:
        result = subprocess.run(
            command,
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    except (FileNotFoundError, PermissionError, OSError):
        return None


def get_git_info(project_path):
    """
    Retrieve Git information from the project

    Args:
        project_path: Project path

    Returns:
        Dictionary of Git information
    """
    info = {}

    # Branch name
    branch = run_git_command(project_path, ['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    info['branch'] = branch if branch else 'unknown'

    # Last commit (relative time and message)
    last_commit = run_git_command(project_path, ['git', 'log', '-1', '--format=%ar|%s'])
    info['last_commit'] = last_commit if last_commit else 'unknown'

    # Last commit timestamp (Unix timestamp: for classification)
    last_commit_time = run_git_command(project_path, ['git', 'log', '-1', '--format=%ct'])
    if last_commit_time and last_commit_time.isdigit():
        info['last_commit_timestamp'] = int(last_commit_time)
    else:
        info['last_commit_timestamp'] = 0

    # Number of changed files
    status_output = run_git_command(project_path, ['git', 'status', '--short'])
    if status_output:
        info['changed_files'] = len(status_output.split('\n'))
    else:
        info['changed_files'] = 0

    return info


def is_worktree(project_path):
    """
    Determine if it's a Git worktree

    .git is a file → worktree
    .git is a directory → normal repository

    Args:
        project_path: Project path

    Returns:
        bool: True if it's a worktree
    """
    git_path = Path(project_path) / ".git"
    return git_path.is_file()


def run_trufflehog_scan(project_path):
    """
    Scan the project with TruffleHog

    Args:
        project_path: Project path

    Returns:
        Dictionary of scan results
    """
    result = {
        "scanned": False,
        "issues_found": 0,
        "has_secrets": False
    }

    # Check if trufflehog command exists
    try:
        subprocess.run(
            ['which', 'trufflehog'],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        # trufflehog is not installed
        return result

    try:
        # Execute trufflehog scan
        scan_result = subprocess.run(
            ['trufflehog', 'git', f'file://{project_path}', '--json', '--no-update'],
            capture_output=True,
            text=True,
            timeout=30  # 30-second timeout
        )

        result["scanned"] = True

        # Parse JSON-formatted output
        if scan_result.stdout:
            lines = scan_result.stdout.strip().split('\n')
            issues_count = 0
            for line in lines:
                try:
                    issue = json.loads(line)
                    if issue:
                        issues_count += 1
                except json.JSONDecodeError:
                    continue

            result["issues_found"] = issues_count
            result["has_secrets"] = issues_count > 0

    except subprocess.TimeoutExpired:
        result["scanned"] = True
        result["timeout"] = True
    except (OSError, PermissionError) as e:
        # Continue scanning even if error occurs
        result["error"] = str(e)

    return result


def read_project_docs(project_path):
    """
    Read project documentation

    Args:
        project_path: Project path

    Returns:
        Dictionary of documentation information (empty dictionary if unable to read)
    """
    docs = {}
    doc_priority = ['CLAUDE.md', 'README.md', 'docs/INDEX.md']

    for doc_name in doc_priority:
        doc_path = Path(project_path) / doc_name
        if doc_path.exists():
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read(2000)  # Read only the first 2000 characters

                    # Simple information extraction (can be improved in the future)
                    if 'Phase' in content or 'phase' in content:
                        # Search for Phase
                        for line in content.split('\n'):
                            if 'Phase' in line or 'phase' in line:
                                docs['phase_hint'] = line.strip()
                                break

                    # Extract overview (first few lines)
                    lines = content.split('\n')
                    overview_lines = []
                    for line in lines[:10]:
                        if line.strip() and not line.startswith('#'):
                            overview_lines.append(line.strip())
                            if len(overview_lines) >= 3:
                                break

                    if overview_lines:
                        docs['overview'] = ' '.join(overview_lines)[:200]

                    break  # Use first found document
            except (UnicodeDecodeError, PermissionError, IOError):
                continue

    return docs


def classify_project(last_commit_timestamp, active_days, inactive_days):
    """
    Classify the project

    Args:
        last_commit_timestamp: Last commit timestamp (Unix timestamp)
        active_days: Number of days for active classification
        inactive_days: Number of days for dormant classification

    Returns:
        Classification ("active", "developing", "dormant")
    """
    if last_commit_timestamp == 0:
        return "unknown"

    now = time.time()
    days_ago = (now - last_commit_timestamp) / (24 * 3600)

    if days_ago <= active_days:
        return "active"
    elif days_ago <= inactive_days:
        return "developing"
    else:
        return "dormant"


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='YPM Project Scanner')
    parser.add_argument(
        '--config', '-c',
        type=str,
        default=None,
        help='Path to config.yml (default: ~/.ypm/config.yml)'
    )
    return parser.parse_args()


def main():
    """Main processing"""
    args = parse_args()

    # Load config.yml
    config = load_config(args.config)

    monitor_config = config.get('monitor', {})
    base_dirs = monitor_config.get('directories', [])
    patterns = monitor_config.get('patterns', ['*'])
    excludes = monitor_config.get('exclude', [])

    classification_config = config.get('classification', {})
    active_days = classification_config.get('active_days', 7)
    inactive_days = classification_config.get('inactive_days', 30)

    # Detect projects
    project_paths = find_projects(base_dirs, patterns, excludes)

    # Collect information for each project
    projects = []
    categories = {"active": 0, "developing": 0, "dormant": 0, "unknown": 0}

    for project_path in project_paths:
        project_name = Path(project_path).name

        # Retrieve Git information
        git_info = get_git_info(project_path)

        # Classify
        category = classify_project(
            git_info['last_commit_timestamp'],
            active_days,
            inactive_days
        )
        categories[category] += 1

        # Retrieve documentation information (active projects only)
        docs = {}
        if category in ["active", "developing"]:
            docs = read_project_docs(project_path)

        # Determine if it's a worktree
        is_wt = is_worktree(project_path)

        # TruffleHog security scan
        security_scan = run_trufflehog_scan(project_path)

        # Add project information
        projects.append({
            "name": project_name,
            "path": project_path,
            "branch": git_info['branch'],
            "last_commit": git_info['last_commit'],
            "changed_files": git_info['changed_files'],
            "category": category,
            "is_worktree": is_wt,
            "docs": docs,
            "security_scan": security_scan
        })

    # Output results in JSON format
    result = {
        "projects": projects,
        "summary": {
            "total": len(projects),
            "active": categories["active"],
            "developing": categories["developing"],
            "dormant": categories["dormant"],
            "unknown": categories["unknown"]
        },
        "scan_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(json.dumps({"error": "Interrupted by user"}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {e}"}), file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
