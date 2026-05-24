"""Evaluation engine for running SAST security audits on GitHub PRs."""

import os
import sys
import subprocess
import shutil
import time
import threading
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
from pathlib import Path

from ..json_parser import parse_json_with_fallbacks

# Timeout constants (in seconds)
TIMEOUT_SHORT = 10
TIMEOUT_GIT_OPERATION = 60
TIMEOUT_FETCH = 600
TIMEOUT_CLONE = 300
TIMEOUT_WORKTREE = 300
TIMEOUT_WORKTREE_CREATE = 1200
TIMEOUT_CLAUDECODE = 1800


@dataclass
class EvalCase:
    """Single evaluation test case."""
    repo_name: str
    pr_number: int
    description: str = ""


@dataclass
class EvalResult:
    """Result of a single evaluation."""
    repo_name: str
    pr_number: int
    description: str
    
    # Evaluation results
    success: bool
    runtime_seconds: float
    findings_count: int
    detected_vulnerabilities: bool
    
    # Optional fields
    error_message: str = ""
    findings_summary: Optional[List[Dict[str, Any]]] = None
    full_findings: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class EvaluationEngine:
    """Engine for running security evaluations on GitHub PRs."""
    
    def __init__(self, work_dir: str = None, verbose: bool = False):
        """Initialize evaluation engine.
        
        Args:
            work_dir: Directory for cloning repositories
            verbose: Enable verbose logging
        """
        # Use ~/code/audit as base directory like pr_audit does
        if work_dir is None:
            work_dir = os.path.expanduser("~/code/audit")
        self.work_dir = work_dir
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)
        
        self.verbose = verbose
        self.claude_api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        
        if not self.claude_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")
        
        # Repository locks for concurrent access
        self._repo_locks: Dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()

        # Get GitHub token from environment or gh CLI
        self.github_token = os.environ.get('GITHUB_TOKEN', '')
        if not self.github_token:
            try:
                result = subprocess.run(['gh', 'auth', 'token'], 
                                      capture_output=True, text=True, timeout=TIMEOUT_GIT_OPERATION)
                if result.returncode == 0:
                    self.github_token = result.stdout.strip()
                    os.environ['GITHUB_TOKEN'] = self.github_token
                    self.log("Retrieved GitHub token from gh CLI")
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                self.log(f"Could not retrieve GitHub token from gh CLI: {e}")

    
    def log(self, message: str, prefix: str = "[EVAL]") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            timestamp = time.strftime('%H:%M:%S')
            print(f"{prefix} [{timestamp}] {message}", file=sys.stderr)
    
    def _get_repo_lock(self, repo_name: str) -> threading.Lock:
        """Get or create a lock for a repository.
        
        Args:
            repo_name: Repository name
            
        Returns:
            Lock for the repository
        """
        with self._locks_lock:
            if repo_name not in self._repo_locks:
                self._repo_locks[repo_name] = threading.Lock()
            return self._repo_locks[repo_name]
    
    def _clean_worktrees(self, repo_path: str, branch_pattern: str = None) -> None:
        """Clean up locked or stale worktrees and remove untracked branches.
        
        Args:
            repo_path: Path to the main repository
            branch_pattern: Optional pattern to match branches for cleanup
        """
        if not os.path.exists(repo_path):
            return
            
        try:
            # First, prune worktrees to clean up stale entries
            subprocess.run(['git', '-C', repo_path, 'worktree', 'prune'], 
                          check=False, capture_output=True, timeout=TIMEOUT_SHORT)
            
            # List all worktrees
            result = subprocess.run(['git', '-C', repo_path, 'worktree', 'list', '--porcelain'],
                                   capture_output=True, text=True, check=True, timeout=TIMEOUT_SHORT)
            
            worktrees = []
            current_worktree = {}
            for line in result.stdout.strip().split('\n'):
                if not line:
                    if current_worktree:
                        worktrees.append(current_worktree)
                        current_worktree = {}
                elif line.startswith('worktree '):
                    current_worktree['path'] = line[9:]
                elif line.startswith('branch '):
                    current_worktree['branch'] = line[7:]
                elif line == 'locked':
                    current_worktree['locked'] = True
            
            if current_worktree:
                worktrees.append(current_worktree)
            
            # Remove locked or matching worktrees
            for wt in worktrees:
                if wt.get('path') == repo_path:
                    continue  # Skip main worktree
                    
                should_remove = False
                if wt.get('locked'):
                    self.log(f"Found locked worktree: {wt.get('path')}")
                    should_remove = True
                elif branch_pattern and 'branch' in wt:
                    branch_name = wt['branch'].replace('refs/heads/', '')
                    if branch_pattern in branch_name:
                        self.log(f"Found matching worktree for cleanup: {wt.get('path')} (branch: {branch_name})")
                        should_remove = True
                
                if should_remove:
                    try:
                        # Force remove the worktree
                        subprocess.run(['git', '-C', repo_path, 'worktree', 'remove', '--force', wt['path']],
                                      check=False, capture_output=True, timeout=TIMEOUT_SHORT)
                        # Also try to remove the directory if it still exists
                        if os.path.exists(wt['path']):
                            shutil.rmtree(wt['path'], ignore_errors=True)
                    except Exception as e:
                        self.log(f"Error removing worktree {wt.get('path')}: {e}")
            
            # Clean up branches
            if branch_pattern:
                # Get all local branches
                result = subprocess.run(['git', '-C', repo_path, 'branch', '--list'],
                                       capture_output=True, text=True, check=True, timeout=TIMEOUT_SHORT)
                
                for line in result.stdout.strip().split('\n'):
                    branch = line.strip().lstrip('* ')
                    if branch_pattern in branch:
                        try:
                            # Delete the branch
                            subprocess.run(['git', '-C', repo_path, 'branch', '-D', branch],
                                          check=False, capture_output=True, timeout=TIMEOUT_SHORT)
                            self.log(f"Deleted branch: {branch}")
                        except Exception as e:
                            self.log(f"Error deleting branch {branch}: {e}")
            
        except Exception as e:
            self.log(f"Error during worktree cleanup: {e}")
    
    def _get_eval_branch_name(self, test_case: EvalCase) -> str:
        """Generate a branch name for evaluation.
        
        Args:
            test_case: Test case being evaluated
            
        Returns:
            Branch name for the evaluation
        """
        # Create a safe branch name from repo and PR
        safe_repo = test_case.repo_name.replace('/', '-').replace('.', '-')
        timestamp = time.strftime('%Y%m%d-%H%M%S')
        return f"eval-pr-{safe_repo}-{test_case.pr_number}-{timestamp}"
    
    def _setup_repository(self, test_case: EvalCase) -> Tuple[bool, str, str]:
        """Set up repository worktree for PR evaluation.
        
        Args:
            test_case: Test case containing repo and PR info
            
        Returns:
            Tuple of (success, worktree_path, error_message)
        """
        repo_name = test_case.repo_name
        pr_number = test_case.pr_number
        
        # Create base path for this repository
        safe_repo_name = repo_name.replace('/', '_')
        base_repo_path = os.path.join(self.work_dir, safe_repo_name)
        
        # Get lock for this repository
        repo_lock = self._get_repo_lock(repo_name)
        
        with repo_lock:
            # Clone or update the base repository
            if not os.path.exists(base_repo_path):
                self.log(f"Cloning {repo_name} to {base_repo_path}")
                clone_url = f"https://github.com/{repo_name}.git"
                if self.github_token:
                    clone_url = f"https://{self.github_token}@github.com/{repo_name}.git"
                
                try:
                    subprocess.run(['git', 'clone', '--filter=blob:none', clone_url, base_repo_path],
                                 check=True, capture_output=True, timeout=TIMEOUT_CLONE)
                except subprocess.CalledProcessError as e:
                    error_msg = f"Failed to clone repository: {e.stderr.decode()}"
                    self.log(error_msg)
                    return False, "", error_msg
            
            # Clean up any stale worktrees for this evaluation
            eval_branch_prefix = f"eval-pr-{safe_repo_name}-{pr_number}"
            self._clean_worktrees(base_repo_path, eval_branch_prefix)
            
            # Create worktree for this specific evaluation
            eval_branch = self._get_eval_branch_name(test_case)
            worktree_path = os.path.join(self.work_dir, f"{safe_repo_name}_pr{pr_number}_{int(time.time())}")
            
            try:
                # Fetch the PR
                self.log(f"Fetching PR #{pr_number} from {repo_name}")
                subprocess.run(['git', '-C', base_repo_path, 'fetch', 'origin', f'pull/{pr_number}/head'],
                             check=True, capture_output=True, timeout=TIMEOUT_FETCH)
                
                # Create new worktree with PR changes
                self.log(f"Creating worktree at {worktree_path}")
                subprocess.run(['git', '-C', base_repo_path, 'worktree', 'add', '-b', eval_branch, 
                              worktree_path, 'FETCH_HEAD'],
                             check=True, capture_output=True, timeout=TIMEOUT_WORKTREE_CREATE)
                
                return True, worktree_path, ""
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to set up worktree: {e.stderr.decode()}"
                self.log(error_msg)
                
                # Clean up failed worktree if it exists
                if os.path.exists(worktree_path):
                    shutil.rmtree(worktree_path, ignore_errors=True)
                
                # Try to remove from git worktree list
                try:
                    subprocess.run(['git', '-C', base_repo_path, 'worktree', 'remove', '--force', worktree_path],
                                 check=False, capture_output=True, timeout=TIMEOUT_SHORT)
                except Exception:
                    pass
                
                return False, "", error_msg
    
    def _cleanup_worktree(self, test_case: EvalCase, worktree_path: str) -> None:
        """Clean up a worktree after evaluation.
        
        Args:
            test_case: Test case that was evaluated
            worktree_path: Path to the worktree
        """
        if not os.path.exists(worktree_path):
            return
            
        repo_name = test_case.repo_name
        safe_repo_name = repo_name.replace('/', '_')
        base_repo_path = os.path.join(self.work_dir, safe_repo_name)
        
        repo_lock = self._get_repo_lock(repo_name)
        
        with repo_lock:
            try:
                # Remove the worktree
                subprocess.run(['git', '-C', base_repo_path, 'worktree', 'remove', '--force', worktree_path],
                             check=False, capture_output=True, timeout=TIMEOUT_WORKTREE)
                
                # Also remove directory if it still exists
                if os.path.exists(worktree_path):
                    shutil.rmtree(worktree_path, ignore_errors=True)
                    
                self.log(f"Cleaned up worktree: {worktree_path}")
                
            except Exception as e:
                self.log(f"Error cleaning up worktree: {e}")
    
    def run_evaluation(self, test_case: EvalCase) -> EvalResult:
        """Run security evaluation on a single PR.
        
        Args:
            test_case: Test case to evaluate
            
        Returns:
            EvalResult with evaluation outcome
        """
        start_time = time.time()
        self.log(f"Starting evaluation of {test_case.repo_name}#{test_case.pr_number}")
        
        # Set up repository
        success, worktree_path, error_msg = self._setup_repository(test_case)
        if not success:
            return EvalResult(
                repo_name=test_case.repo_name,
                pr_number=test_case.pr_number,
                description=test_case.description,
                success=False,
                runtime_seconds=time.time() - start_time,
                findings_count=0,
                detected_vulnerabilities=False,
                error_message=f"Repository setup failed: {error_msg}"
            )
        
        try:
            # Run the SAST audit
            self.log(f"Running SAST audit on {worktree_path}")
            audit_success, output, parsed_results, error_message = self._run_sast_audit(test_case, worktree_path)
            
            if not audit_success:
                return EvalResult(
                    repo_name=test_case.repo_name,
                    pr_number=test_case.pr_number,
                    description=test_case.description,
                    success=False,
                    runtime_seconds=time.time() - start_time,
                    findings_count=0,
                    detected_vulnerabilities=False,
                    error_message=f"SAST audit failed: {error_message or 'Unknown error'}"
                )
            
            # Extract findings from results
            findings = []
            if parsed_results and 'findings' in parsed_results:
                findings = parsed_results['findings']
            
            findings_count = len(findings)
            detected_vulnerabilities = findings_count > 0
            
            # Create findings summary
            findings_summary = []
            for finding in findings[:10]:  # Limit to first 10 for summary
                summary_item = {
                    'file': finding.get('file', finding.get('path', 'unknown')),
                    'line': finding.get('line', finding.get('start', {}).get('line', 0)),
                    'severity': finding.get('severity', 'UNKNOWN'),
                    'title': finding.get('check_id', finding.get('category', 'Unknown')),
                    'description': finding.get('description', finding.get('message', 'Unknown'))
                }
                findings_summary.append(summary_item)
            
            return EvalResult(
                repo_name=test_case.repo_name,
                pr_number=test_case.pr_number,
                description=test_case.description,
                success=True,
                runtime_seconds=time.time() - start_time,
                findings_count=findings_count,
                detected_vulnerabilities=detected_vulnerabilities,
                findings_summary=findings_summary,
                full_findings=findings
            )
            
        finally:
            # Always clean up the worktree
            self._cleanup_worktree(test_case, worktree_path)
    
    def _run_sast_audit(self, test_case: EvalCase, repo_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]], Optional[str]]:
        """Run the SAST audit script on a repository.
        
        Args:
            test_case: Test case being evaluated
            repo_path: Path to the repository
            
        Returns:
            Tuple of (success, output, parsed_results, error_message)
        """
        # Prepare environment
        env = os.environ.copy()
        env['GITHUB_REPOSITORY'] = test_case.repo_name
        env['PR_NUMBER'] = str(test_case.pr_number)
        env['ANTHROPIC_API_KEY'] = self.claude_api_key
        if self.github_token:
            env['GITHUB_TOKEN'] = self.github_token
        env['EVAL_MODE'] = '1'  # Enable eval mode
        
        # Run the audit script
        script_path = Path(__file__).parent.parent / 'github_action_audit.py'
        
        # Add the project root to PYTHONPATH so claudecode module can be imported
        project_root = script_path.parent.parent
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = str(project_root)
        
        try:
            self.log(f"Executing SAST audit for PR #{test_case.pr_number}")
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=repo_path,
                env=env,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_CLAUDECODE
            )
            
            output = result.stdout
            
            # Parse the JSON output first to see if we got valid results
            success, parsed_results = parse_json_with_fallbacks(output)
            if not success:
                self.log("Failed to parse SAST audit output as JSON")
                # If we can't parse JSON and have non-zero exit code, it's a real failure
                if result.returncode != 0:
                    error_output = result.stderr or output
                    self.log(f"SAST audit failed with return code {result.returncode}")
                    self.log(f"Error output: {error_output[:500]}...")
                    return False, output, None, f"Exit code {result.returncode}: {error_output[:200]}"
                return False, output, None, "Invalid JSON output"
            
            # If we got valid JSON output, we consider it successful even with exit code 1
            # (exit code 1 means high-severity findings were found)
            if result.returncode not in [0, 1]:
                error_output = result.stderr or output
                self.log(f"SAST audit failed with unexpected return code {result.returncode}")
                self.log(f"Error output: {error_output[:500]}...")
                return False, output, None, f"Unexpected exit code {result.returncode}: {error_output[:200]}"
            
            return True, output, parsed_results, None
            
        except subprocess.TimeoutExpired:
            self.log(f"SAST audit timed out after {TIMEOUT_CLAUDECODE} seconds")
            return False, "", None, f"Timeout after {TIMEOUT_CLAUDECODE} seconds"
        except Exception as e:
            self.log(f"Exception during SAST audit: {e}")
            return False, "", None, str(e)


def run_single_evaluation(test_case: EvalCase, verbose: bool = False, work_dir: str = None) -> EvalResult:
    """Convenience function to run a single evaluation.
    
    Args:
        test_case: Test case to evaluate
        verbose: Enable verbose logging
        work_dir: Directory for temporary files
        
    Returns:
        EvalResult
    """
    engine = EvaluationEngine(work_dir=work_dir, verbose=verbose)
    return engine.run_evaluation(test_case)