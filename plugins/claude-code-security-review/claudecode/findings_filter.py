"""Findings filter for reducing false positives in security audit results."""

import re
from typing import Dict, Any, List, Tuple, Optional, Pattern
import time
from dataclasses import dataclass, field

from claudecode.claude_api_client import ClaudeAPIClient
from claudecode.constants import DEFAULT_CLAUDE_MODEL
from claudecode.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FilterStats:
    """Statistics about the filtering process."""
    total_findings: int = 0
    hard_excluded: int = 0
    claude_excluded: int = 0
    kept_findings: int = 0
    exclusion_breakdown: Dict[str, int] = field(default_factory=dict)
    confidence_scores: List[float] = field(default_factory=list)
    runtime_seconds: float = 0.0


class HardExclusionRules:
    """Hard exclusion rules for common false positives."""
    
    # Pre-compiled regex patterns for better performance
    _DOS_PATTERNS: List[Pattern] = [
        re.compile(r'\b(denial of service|dos attack|resource exhaustion)\b', re.IGNORECASE),
        re.compile(r'\b(exhaust|overwhelm|overload).*?(resource|memory|cpu)\b', re.IGNORECASE),
        re.compile(r'\b(infinite|unbounded).*?(loop|recursion)\b', re.IGNORECASE),
    ]
    
    
    _RATE_LIMITING_PATTERNS: List[Pattern] = [
        re.compile(r'\b(missing|lack of|no)\s+rate\s+limit', re.IGNORECASE),
        re.compile(r'\brate\s+limiting\s+(missing|required|not implemented)', re.IGNORECASE),
        re.compile(r'\b(implement|add)\s+rate\s+limit', re.IGNORECASE),
        re.compile(r'\bunlimited\s+(requests|calls|api)', re.IGNORECASE),
    ]
    
    _RESOURCE_PATTERNS: List[Pattern] = [
        re.compile(r'\b(resource|memory|file)\s+leak\s+potential', re.IGNORECASE),
        re.compile(r'\bunclosed\s+(resource|file|connection)', re.IGNORECASE),
        re.compile(r'\b(close|cleanup|release)\s+(resource|file|connection)', re.IGNORECASE),
        re.compile(r'\bpotential\s+memory\s+leak', re.IGNORECASE),
        re.compile(r'\b(database|thread|socket|connection)\s+leak', re.IGNORECASE),
    ]
    
    _OPEN_REDIRECT_PATTERNS: List[Pattern] = [
        re.compile(r'\b(open redirect|unvalidated redirect)\b', re.IGNORECASE),
        re.compile(r'\b(redirect.(attack|exploit|vulnerability))\b', re.IGNORECASE),
        re.compile(r'\b(malicious.redirect)\b', re.IGNORECASE),
    ]
    
    _MEMORY_SAFETY_PATTERNS: List[Pattern] = [
        re.compile(r'\b(buffer overflow|stack overflow|heap overflow)\b', re.IGNORECASE),
        re.compile(r'\b(oob)\s+(read|write|access)\b', re.IGNORECASE),
        re.compile(r'\b(out.?of.?bounds?)\b', re.IGNORECASE),
        re.compile(r'\b(memory safety|memory corruption)\b', re.IGNORECASE),
        re.compile(r'\b(use.?after.?free|double.?free|null.?pointer.?dereference)\b', re.IGNORECASE),
        re.compile(r'\b(segmentation fault|segfault|memory violation)\b', re.IGNORECASE),
        re.compile(r'\b(bounds check|boundary check|array bounds)\b', re.IGNORECASE),
        re.compile(r'\b(integer overflow|integer underflow|integer conversion)\b', re.IGNORECASE),
        re.compile(r'\barbitrary.?(memory read|pointer dereference|memory address|memory pointer)\b', re.IGNORECASE),
    ]

    _REGEX_INJECTION: List[Pattern] = [
        re.compile(r'\b(regex|regular expression)\s+injection\b', re.IGNORECASE),
        re.compile(r'\b(regex|regular expression)\s+denial of service\b', re.IGNORECASE),
        re.compile(r'\b(regex|regular expression)\s+flooding\b', re.IGNORECASE),
    ]
    
    _SSRF_PATTERNS: List[Pattern] = [
        re.compile(r'\b(ssrf|server\s+.?side\s+.?request\s+.?forgery)\b', re.IGNORECASE),
    ]
    
    @classmethod
    def get_exclusion_reason(cls, finding: Dict[str, Any]) -> Optional[str]:
        """Check if a finding should be excluded based on hard rules.
        
        Args:
            finding: Security finding to check
            
        Returns:
            Exclusion reason if finding should be excluded, None otherwise
        """
        # Check if finding is in a Markdown file
        file_path = finding.get('file', '')
        if file_path.lower().endswith('.md'):
            return "Finding in Markdown documentation file"
        
        description = finding.get('description', '')
        title = finding.get('title', '')
        
        # Handle None values
        if description is None:
            description = ''
        if title is None:
            title = ''
            
        combined_text = f"{title} {description}".lower()
        
        # Check DOS patterns
        for pattern in cls._DOS_PATTERNS:
            if pattern.search(combined_text):
                return "Generic DOS/resource exhaustion finding (low signal)"
        
        
        # Check rate limiting patterns  
        for pattern in cls._RATE_LIMITING_PATTERNS:
            if pattern.search(combined_text):
                return "Generic rate limiting recommendation"
        
        # Check resource patterns - always exclude
        for pattern in cls._RESOURCE_PATTERNS:
            if pattern.search(combined_text):
                return "Resource management finding (not a security vulnerability)"
        
        # Check open redirect patterns
        for pattern in cls._OPEN_REDIRECT_PATTERNS:
            if pattern.search(combined_text):
                return "Open redirect vulnerability (not high impact)"
            
        # Check regex injection patterns
        for pattern in cls._REGEX_INJECTION:
            if pattern.search(combined_text):
                return "Regex injection finding (not applicable)"
        
        # Check memory safety patterns - exclude if NOT in C/C++ files
        c_cpp_extensions = {'.c', '.cc', '.cpp', '.h'}
        file_ext = ''
        if '.' in file_path:
            file_ext = f".{file_path.lower().split('.')[-1]}"
        
        # If file doesn't have a C/C++ extension (including no extension), exclude memory safety findings
        if file_ext not in c_cpp_extensions:
            for pattern in cls._MEMORY_SAFETY_PATTERNS:
                if pattern.search(combined_text):
                    return "Memory safety finding in non-C/C++ code (not applicable)"
        
        # Check SSRF patterns - exclude if in HTML files only
        html_extensions = {'.html'}
        
        # If file has HTML extension, exclude SSRF findings
        if file_ext in html_extensions:
            for pattern in cls._SSRF_PATTERNS:
                if pattern.search(combined_text):
                    return "SSRF finding in HTML file (not applicable to client-side code)"
        
        return None


class FindingsFilter:
    """Main filter class for security findings."""
    
    def __init__(self, 
                 use_hard_exclusions: bool = True,
                 use_claude_filtering: bool = True,
                 api_key: Optional[str] = None,
                 model: str = DEFAULT_CLAUDE_MODEL,
                 custom_filtering_instructions: Optional[str] = None):
        """Initialize findings filter.
        
        Args:
            use_hard_exclusions: Whether to apply hard exclusion rules
            use_claude_filtering: Whether to use Claude API for filtering
            api_key: Anthropic API key for Claude filtering
            model: Claude model to use for filtering
            custom_filtering_instructions: Optional custom filtering instructions
        """
        self.use_hard_exclusions = use_hard_exclusions
        self.use_claude_filtering = use_claude_filtering
        self.custom_filtering_instructions = custom_filtering_instructions
        
        # Initialize Claude client if filtering is enabled
        self.claude_client = None
        if self.use_claude_filtering:
            try:
                self.claude_client = ClaudeAPIClient(
                    model=model,
                    api_key=api_key
                )
                # Validate API access
                valid, error = self.claude_client.validate_api_access()
                if not valid:
                    logger.warning(f"Claude API validation failed: {error}")
                    self.claude_client = None
                    self.use_claude_filtering = False
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {str(e)}")
                self.use_claude_filtering = False
    
    def filter_findings(self, 
                       findings: List[Dict[str, Any]],
                       pr_context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any], FilterStats]:
        """Filter security findings to remove false positives.
        
        Args:
            findings: List of security findings from Claude Code audit
            pr_context: Optional PR context for better analysis
            
        Returns:
            Tuple of (success, filtered_results, stats)
        """
        start_time = time.time()
        
        if not findings:
            stats = FilterStats(total_findings=0, runtime_seconds=0.0)
            return True, {
                "filtered_findings": [],
                "excluded_findings": [],
                "analysis_summary": {
                    "total_findings": 0,
                    "kept_findings": 0,
                    "excluded_findings": 0,
                    "exclusion_breakdown": {}
                }
            }, stats
        
        logger.info(f"Filtering {len(findings)} security findings")
        
        # Initialize statistics
        stats = FilterStats(total_findings=len(findings))
        
        # Step 1: Apply hard exclusion rules
        findings_after_hard = []
        excluded_hard = []
        
        if self.use_hard_exclusions:
            for i, finding in enumerate(findings):
                exclusion_reason = HardExclusionRules.get_exclusion_reason(finding)
                if exclusion_reason:
                    excluded_hard.append({
                        "finding": finding,
                        "index": i,
                        "exclusion_reason": exclusion_reason,
                        "filter_stage": "hard_rules"
                    })
                    stats.hard_excluded += 1
                    
                    # Track exclusion breakdown
                    key = exclusion_reason.split('(')[0].strip()
                    stats.exclusion_breakdown[key] = stats.exclusion_breakdown.get(key, 0) + 1
                else:
                    findings_after_hard.append((i, finding))
            
            logger.info(f"Hard exclusions removed {stats.hard_excluded} findings")
        else:
            findings_after_hard = [(i, f) for i, f in enumerate(findings)]
        
        # Step 2: Apply Claude API filtering if enabled
        findings_after_claude = []
        excluded_claude = []
        
        if self.use_claude_filtering and self.claude_client and findings_after_hard:
            # Process findings individually
            logger.info(f"Processing {len(findings_after_hard)} findings individually through Claude API")
            
            for orig_idx, finding in findings_after_hard:
                # Call Claude API for single finding
                success, analysis_result, error_msg = self.claude_client.analyze_single_finding(
                    finding, pr_context, self.custom_filtering_instructions
                )
                
                if success and analysis_result:
                    # Process Claude's analysis for single finding
                    confidence = analysis_result.get('confidence_score', 10.0)
                    keep_finding = analysis_result.get('keep_finding', True)
                    justification = analysis_result.get('justification', '')
                    exclusion_reason = analysis_result.get('exclusion_reason')
                    
                    stats.confidence_scores.append(confidence)
                    
                    if not keep_finding:
                        # Claude recommends excluding
                        excluded_claude.append({
                            "finding": finding,
                            "confidence_score": confidence,
                            "exclusion_reason": exclusion_reason or f"Low confidence score: {confidence}",
                            "justification": justification,
                            "filter_stage": "claude_api"
                        })
                        stats.claude_excluded += 1
                    else:
                        # Keep finding with metadata
                        enriched_finding = finding.copy()
                        enriched_finding['_filter_metadata'] = {
                            'confidence_score': confidence,
                            'justification': justification,
                        }
                        findings_after_claude.append(enriched_finding)
                        stats.kept_findings += 1
                else:
                    # Claude API call failed for this finding - keep it with warning
                    logger.warning(f"Claude API call failed for finding {orig_idx}: {error_msg}")
                    enriched_finding = finding.copy()
                    enriched_finding['_filter_metadata'] = {
                        'confidence_score': 10.0,  # Default high confidence
                        'justification': f'Claude API failed: {error_msg}',
                    }
                    findings_after_claude.append(enriched_finding)
                    stats.kept_findings += 1
        else:
            # Claude filtering disabled or no client - keep all findings from hard filter
            for orig_idx, finding in findings_after_hard:
                enriched_finding = finding.copy()
                enriched_finding['_filter_metadata'] = {
                    'confidence_score': 10.0,  # Default high confidence
                    'justification': 'Claude filtering disabled',
                }
                findings_after_claude.append(enriched_finding)
                stats.kept_findings += 1
        
        # Combine all excluded findings
        all_excluded = excluded_hard + excluded_claude
        
        # Calculate final statistics
        stats.runtime_seconds = time.time() - start_time
        
        # Build filtered results
        filtered_results = {
            "filtered_findings": findings_after_claude,
            "excluded_findings": all_excluded,
            "analysis_summary": {
                "total_findings": stats.total_findings,
                "kept_findings": stats.kept_findings,
                "excluded_findings": len(all_excluded),
                "hard_excluded": stats.hard_excluded,
                "claude_excluded": stats.claude_excluded,
                "exclusion_breakdown": stats.exclusion_breakdown,
                "average_confidence": sum(stats.confidence_scores) / len(stats.confidence_scores) if stats.confidence_scores else None,
                "runtime_seconds": stats.runtime_seconds
            }
        }
        
        logger.info(f"Filtering completed: {stats.kept_findings}/{stats.total_findings} findings kept "
                    f"({stats.runtime_seconds:.1f}s)")
        
        return True, filtered_results, stats
