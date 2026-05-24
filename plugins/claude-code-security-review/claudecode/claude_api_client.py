"""Claude API client for direct Anthropic API calls."""

import os
import json
import time
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

from anthropic import Anthropic

from claudecode.constants import (
    DEFAULT_CLAUDE_MODEL, DEFAULT_TIMEOUT_SECONDS, DEFAULT_MAX_RETRIES,
    RATE_LIMIT_BACKOFF_MAX, PROMPT_TOKEN_LIMIT,
)
from claudecode.json_parser import parse_json_with_fallbacks
from claudecode.logger import get_logger

logger = get_logger(__name__)


class ClaudeAPIClient:
    """Client for calling Claude API directly for security analysis tasks."""
    
    def __init__(self, 
                 model: Optional[str] = None,
                 api_key: Optional[str] = None,
                 timeout_seconds: Optional[int] = None,
                 max_retries: Optional[int] = None):
        """Initialize Claude API client.
        
        Args:
            model: Claude model to use
            api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum retry attempts for API calls
        """
        self.model = model or DEFAULT_CLAUDE_MODEL
        self.timeout_seconds = timeout_seconds or DEFAULT_TIMEOUT_SECONDS
        self.max_retries = max_retries or DEFAULT_MAX_RETRIES
        
        # Get API key from environment or parameter
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No Anthropic API key found. Please set ANTHROPIC_API_KEY environment variable "
                "or provide api_key parameter."
            )
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)
        logger.info("Claude API client initialized successfully")
    
    def validate_api_access(self) -> Tuple[bool, str]:
        """Validate that API access is working.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Simple test call to verify API access
            self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}],
                timeout=10
            )
            logger.info("Claude API access validated successfully")
            return True, ""
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Claude API validation failed: {error_msg}")
            return False, f"API validation failed: {error_msg}"
    
    def call_with_retry(self, 
                       prompt: str,
                       system_prompt: Optional[str] = None,
                       max_tokens: int = PROMPT_TOKEN_LIMIT) -> Tuple[bool, str, str]:
        """Make Claude API call with retry logic.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (success, response_text, error_message)
        """
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                logger.info(f"Claude API call attempt {retries + 1}/{self.max_retries + 1}")
                
                # Prepare messages
                messages = [{"role": "user", "content": prompt}]
                
                # Build API call parameters
                api_params = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": messages,
                    "timeout": self.timeout_seconds
                }
                
                if system_prompt:
                    api_params["system"] = system_prompt
                
                # Make API call
                start_time = time.time()
                response = self.client.messages.create(**api_params)
                duration = time.time() - start_time
                
                # Extract text from response
                response_text = ""
                for content_block in response.content:
                    if hasattr(content_block, 'text'):
                        response_text += content_block.text
                
                logger.info(f"Claude API call successful in {duration:.1f}s")
                return True, response_text, ""
                
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                logger.error(f"Claude API call failed: {error_msg}")
                
                # Check if it's a rate limit error
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    logger.warning("Rate limit detected, increasing backoff")
                    backoff_time = min(RATE_LIMIT_BACKOFF_MAX, 5 * (retries + 1))  # Progressive backoff
                    time.sleep(backoff_time)
                elif "timeout" in error_msg.lower():
                    logger.warning("Timeout detected, retrying")
                    time.sleep(2)
                else:
                    # For other errors, shorter backoff
                    time.sleep(1)
                
                retries += 1
        
        # All retries exhausted
        return False, "", f"API call failed after {self.max_retries + 1} attempts: {last_error}"
    
    def analyze_single_finding(self, 
                              finding: Dict[str, Any], 
                              pr_context: Optional[Dict[str, Any]] = None,
                              custom_filtering_instructions: Optional[str] = None) -> Tuple[bool, Dict[str, Any], str]:
        """Analyze a single security finding to filter false positives using Claude API.
        
        Args:
            finding: Single security finding to analyze
            pr_context: Optional PR context for better analysis
            
        Returns:
            Tuple of (success, analysis_result, error_message)
        """
        try:
            # Generate analysis prompt with file content
            prompt = self._generate_single_finding_prompt(finding, pr_context, custom_filtering_instructions)
            system_prompt = self._generate_system_prompt()
            
            # Call Claude API
            success, response_text, error_msg = self.call_with_retry(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=PROMPT_TOKEN_LIMIT 
            )
            
            if not success:
                return False, {}, error_msg
            
            # Parse JSON response using json_parser
            success, analysis_result = parse_json_with_fallbacks(response_text, "Claude API response")
            if success:
                logger.info("Successfully parsed Claude API response for single finding")
                return True, analysis_result, ""
            else:
                # Fallback: return error
                return False, {}, "Failed to parse JSON response"
                
        except Exception as e:
            logger.exception(f"Error during single finding security analysis: {str(e)}")
            return False, {}, f"Single finding security analysis failed: {str(e)}"

    
    def _generate_system_prompt(self) -> str:
        """Generate system prompt for security analysis."""
        return """You are a security expert reviewing findings from an automated code audit tool.
Your task is to filter out false positives and low-signal findings to reduce alert fatigue.
You must maintain high recall (don't miss real vulnerabilities) while improving precision.

Respond ONLY with valid JSON in the exact format specified in the user prompt.
Do not include explanatory text, markdown formatting, or code blocks."""
    
    def _generate_single_finding_prompt(self, 
                                       finding: Dict[str, Any], 
                                       pr_context: Optional[Dict[str, Any]] = None,
                                       custom_filtering_instructions: Optional[str] = None) -> str:
        """Generate prompt for analyzing a single security finding.
        
        Args:
            finding: Single security finding
            pr_context: Optional PR context
            
        Returns:
            Formatted prompt string
        """
        pr_info = ""
        if pr_context and isinstance(pr_context, dict):
            pr_info = f"""
PR Context:
- Repository: {pr_context.get('repo_name', 'unknown')}
- PR #{pr_context.get('pr_number', 'unknown')}
- Title: {pr_context.get('title', 'unknown')}
- Description: {(pr_context.get('description') or 'No description')[:500]}...
"""
        
        # Get file content if available
        file_path = finding.get('file', '')
        file_content = ""
        if file_path:
            success, content, error = self._read_file(file_path)
            if success:
                file_content = f"""

File Content ({file_path}):
```
{content}
```"""
            else:
                file_content = f"""

File Content ({file_path}): Error reading file - {error}
"""
        
        finding_json = json.dumps(finding, indent=2)
        
        # Use custom filtering instructions if provided, otherwise use defaults
        if custom_filtering_instructions:
            filtering_section = custom_filtering_instructions
        else:
            filtering_section = """HARD EXCLUSIONS - Automatically exclude findings matching these patterns:
1. Denial of Service (DOS) vulnerabilities or resource exhaustion attacks
2. Secrets/credentials stored on disk (these are managed separately) 
3. Rate limiting concerns or service overload scenarios (services don't need to implement rate limiting)
4. Memory consumption or CPU exhaustion issues
5. Lack of input validation on non-security-critical fields without proven security impact
6. Input sanitization concerns for github action workflows
7. A lack of hardening measures. Code is not expected to implement all security best practices, just avoid obvious vulnerabilities.
8. Race conditions or timing attacks that are theoretical rather than practical issues. Only report a race condition if it is extremely problematic.
9. Vulnerabilities related to outdated third-party libraries. These are managed separately and should not be reported here.
10. Memory safety issues such as buffer overflows or use-after-free-vulnerabilities are impossible in rust. Do not report memory safety issues in rust code.
11. Files that are only unit tests or only used as part of running tests.
12. Log spoofing concerns. Outputing un-sanitized user input to logs is not a vulnerability.
13. SSRF vulnerabilities that only control the path. SSRF is only a concern if it can control the host or protocol.
14. Including user-controlled content in AI system prompts is not a vulnerability. In general, the inclusion of user input in an AI prompt is not a vulnerability.
15. Do not report issues related to adding a dependency to a project that is not available from the relevant package repository. Depending on internal libraries that are not publicly available is not a vulnerability.
16. Do not report issues that cause the code to crash, but are not actually a vulnerability. E.g. a variable that is undefined or null is not a vulnerability.

SIGNAL QUALITY CRITERIA - For remaining findings, assess:
1. Is there a concrete, exploitable vulnerability with a clear attack path?
2. Does this represent a real security risk vs theoretical best practice?
3. Are there specific code locations and reproduction steps?
4. Would this finding be actionable for a security team?

PRECEDENTS - 
1. Logging high value secrets in plaintext is a vulnerability. Otherwise, do not report issues around theoretical exposures of secrets. Logging URLs is assumed to be safe. Logging request headers is assumed to be dangerous since they likely contain credentials.
2. UUIDs can be assumed to be unguessable and do not need to be validated. If a vulnerabilities requires guessing a UUID, it is not a valid vulnerability.
3. Audit logs are not a critical security feature and should not be reported as a vulnerability if they are missing or modified.
4. Environment variables and CLI flags are trusted values. Attackers are not able to modify them in a secure environment. Any attack that relies on controlling an environment variable is invalid.
5. Resource management issues such as memory or file descriptor leaks are not valid.
6. Subtle or low impact web vulnerabilities such as tabnabbing, XS-Leaks, prototype pollution, and open redirects are not valid.
7. Vulnerabilities related to outdated third-party libraries. These are managed separately and should not be reported here.
8. React is generally secure against XSS. React does not need to sanitize or escape user input unless it is using dangerouslySetInnerHTML or similar methods. Do not report XSS vulnerabilities in React components or tsx files unless they are using unsafe methods.
9. Most vulnerabilities in github action workflows are not exploitable in practice. Before validating a github action workflow vulnerability ensure it is concrete and has a very specific attack path.
10. A lack of permission checking or authentication in client-side TS code is not a vulnerability. Client-side code is not trusted and does not need to implement these checks, they are handled on the server-side. The same applies to all flows that send untrusted data to the backend, the backend is responsible for validating and sanitizing all inputs.
11. Only include MEDIUM findings if they are obvious and concrete issues.
12. Most vulnerabilities in ipython notebooks (*.ipynb files) are not exploitable in practice. Before validating a notebook vulnerability ensure it is concrete and has a very specific attack path.
13. Logging non-PII data is not a vulnerability even if the data may be sensitive. Only report logging vulnerabilities if they expose sensitive information such as secrets, passwords, or personally identifiable information (PII).
14. Command injection vulnerabilities in shell scripts are generally not exploitable in practice since shell scripts generally do not run with untrusted user input. Only report command injection vulnerabilities in shell scripts if they are concrete and have a very specific attack path for untrusted input.
15. SSRF (Server-Side Request Forgery) vulnerabilities in client-side JavaScript/TypeScript files (.js, .ts, .tsx, .jsx) are not valid since client-side code cannot make server-side requests that would bypass firewalls or access internal resources. Only report SSRF in server-side code (e.g. Python or JS that is known to run on the server-side). The same logic applies to path-traversal attacks, they are not a problem in client-side JS.
16. Path traversal attacks using ../ are generally not a problem when triggering HTTP requests. These are generally only relevant when reading files where the ../ may allow accessing unintended files.
17. Injecting into log queries is generally not an issue. Only report this if the injection will definitely lead to exposing sensitive data to external users."""
        
        return f"""I need you to analyze a security finding from an automated code audit and determine if it's a false positive.

{pr_info}

{filtering_section}

Assign a confidence score from 1-10:
- 1-3: Low confidence, likely false positive or noise
- 4-6: Medium confidence, needs investigation  
- 7-10: High confidence, likely true vulnerability

Finding to analyze:
```json
{finding_json}
```
{file_content}

Respond with EXACTLY this JSON structure (no markdown, no code blocks):
{{
  "original_severity": "HIGH",
  "confidence_score": 8,
  "keep_finding": true,
  "exclusion_reason": null,
  "justification": "Clear SQL injection vulnerability with specific exploit path"
}}"""

    
    def _read_file(self, file_path: str) -> Tuple[bool, str, str]:
        """Read a file and format it with line numbers.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Tuple of (success, formatted_content, error_message)
        """
        try:
            # Check if REPO_PATH is set and use it as base path
            repo_path = os.environ.get('REPO_PATH')
            if repo_path:
                # Convert file_path to Path and check if it's absolute
                path = Path(file_path)
                if not path.is_absolute():
                    # Make it relative to REPO_PATH
                    path = Path(repo_path) / file_path
            else:
                path = Path(file_path)
            
            if not path.exists():
                return False, "", f"File not found: {path}"
            
            if not path.is_file():
                return False, "", f"Path is not a file: {path}"
            
            # Read file with error handling for encoding issues
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with latin-1 encoding as fallback
                with open(path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            return True, content, ""
            
        except Exception as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg


def get_claude_api_client(model: str = DEFAULT_CLAUDE_MODEL,
                         api_key: Optional[str] = None,
                         timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> ClaudeAPIClient:
    """Convenience function to get Claude API client.
    
    Args:
        model: Claude model identifier
        api_key: Optional API key (reads from environment if not provided)
        timeout_seconds: API call timeout
        
    Returns:
        Initialized ClaudeAPIClient instance
    """
    return ClaudeAPIClient(
        model=model,
        api_key=api_key,
        timeout_seconds=timeout_seconds
    )


