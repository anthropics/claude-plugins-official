"""Unit tests for HardExclusionRules in findings_filter module."""

from claudecode.findings_filter import HardExclusionRules


class TestHardExclusionRules:
    """Test the HardExclusionRules class for filtering false positives."""
    
    def test_dos_pattern_exclusion(self):
        """Test exclusion of DOS-related findings."""
        dos_findings = [
            {
                "title": "Potential Denial of Service",
                "description": "This could lead to resource exhaustion"
            },
            {
                "title": "Resource consumption issue",
                "description": "Unbounded loop could exhaust CPU resources"
            },
            {
                "title": "Memory exhaustion",
                "description": "This function could overwhelm memory with large inputs"
            },
            {
                "title": "Stack overflow vulnerability",
                "description": "Infinite recursion detected"
            }
        ]
        
        for finding in dos_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert "DOS/resource exhaustion" in reason
    
    def test_dos_pattern_not_excluded_with_exploit(self):
        """Test that stack overflow with exploit mention is not excluded."""
        finding = {
            "title": "Stack overflow exploit",
            "description": "This stack overflow can be exploited to execute arbitrary code",
            "file": "exploit.c"  # Add C file so it's not excluded by memory safety rule
        }
        
        reason = HardExclusionRules.get_exclusion_reason(finding)
        assert reason is None  # Should not be excluded
    
    def test_generic_validation_pattern_exclusion(self):
        """Test that generic validation findings are NOT excluded anymore."""
        validation_findings = [
            {
                "title": "Security Issue",
                "description": "Missing input validation"
            },
            {
                "title": "Security Issue", 
                "description": "Input validation required"
            },
            {
                "title": "Security Issue",
                "description": "Validate parameters"
            },
            {
                "title": "Security Issue",
                "description": "Add input validation"
            }
        ]
        
        # Since we removed generic validation patterns, these should NOT be excluded
        for finding in validation_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is None
    
    def test_specific_validation_not_excluded(self):
        """Test that specific validation issues are not excluded."""
        specific_findings = [
            {
                "title": "Missing input validation",
                "description": "SQL injection possible due to missing validation"
            },
            {
                "title": "No validation",
                "description": "Command injection vulnerability - validate shell commands"
            },
            {
                "title": "Missing validation",
                "description": "Path traversal - validate file paths"
            },
            {
                "title": "Add validation",
                "description": "Eval() used without input validation"
            }
        ]
        
        for finding in specific_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is None  # Should not be excluded due to specific context
    
    def test_secrets_pattern_exclusion(self):
        """Test that generic secrets warnings are NOT excluded anymore."""
        secrets_findings = [
            {
                "title": "Hardcoded password detected",
                "description": "Avoid hardcoding credentials in source code"
            },
            {
                "title": "Plaintext secrets",
                "description": "Credentials stored in plaintext"
            },
            {
                "title": "Embedded token",
                "description": "API key in source code"
            },
            {
                "title": "Password storage",
                "description": "Password stored in clear text"
            }
        ]
        
        # Since we removed secrets patterns, these should NOT be excluded
        for finding in secrets_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is None
    
    def test_actual_secrets_not_excluded(self):
        """Test that actual exposed secrets are not excluded."""
        actual_secrets = [
            {
                "title": "Hardcoded password",
                "description": "Found actual password: 'admin123' in config file"
            },
            {
                "title": "API key exposed",
                "description": "Discovered API key in source: sk-1234567890"
            },
            {
                "title": "Plaintext password",
                "description": "Database password 'mypass' found in code"
            }
        ]
        
        for finding in actual_secrets:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is None  # Should not be excluded
    
    def test_rate_limiting_pattern_exclusion(self):
        """Test exclusion of rate limiting recommendations."""
        rate_limit_findings = [
            {
                "title": "Missing rate limit",
                "description": "API endpoint has no rate limiting"
            },
            {
                "title": "Rate limiting required",
                "description": "Implement rate limiting for this endpoint"
            },
            {
                "title": "No rate limit",
                "description": "Unlimited requests allowed"
            },
            {
                "title": "Add rate limiting",
                "description": "This API needs rate limits"
            }
        ]
        
        for finding in rate_limit_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert "rate limiting recommendation" in reason
    
    def test_resource_pattern_exclusion(self):
        """Test exclusion of generic resource management findings."""
        resource_findings = [
            {
                "title": "Security Issue",
                "description": "Potential memory leak detected"
            },
            {
                "title": "Security Issue",
                "description": "Resource leak potential in file handling"
            },
            {
                "title": "Security Issue",
                "description": "Unclosed resource detected in function"
            },
            {
                "title": "Security Issue",
                "description": "File cleanup required - close resource"
            }
        ]
        
        for finding in resource_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert "Resource management finding" in reason
    
    def test_specific_resource_also_excluded(self):
        """Test that ALL resource issues are now excluded (including specific ones)."""
        specific_resources = [
            {
                "title": "Database connection leak",
                "description": "PostgreSQL connections not returned to pool"
            },
            {
                "title": "Thread leak",
                "description": "Thread pool exhaustion due to unclosed threads"
            },
            {
                "title": "Socket leak",
                "description": "TCP sockets remain open after errors"
            }
        ]
        
        # All resource issues should be excluded now
        for finding in specific_resources:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert "Resource management finding" in reason  # Should not be excluded
    
    def test_open_redirect_pattern_exclusion(self):
        """Test exclusion of open redirect findings."""
        redirect_findings = [
            {
                "title": "Open redirect vulnerability",
                "description": "User input used in redirect without validation"
            },
            {
                "title": "Unvalidated redirect",
                "description": "Redirect URL not validated"
            },
            {
                "title": "Redirect vulnerability",
                "description": "Possible redirect attack"
            },
            {
                "title": "Malicious redirect possible",
                "description": "User-controlled redirect parameter"
            }
        ]
        
        for finding in redirect_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert "Open redirect" in reason
    
    def test_mixed_case_handling(self):
        """Test that pattern matching handles mixed case correctly."""
        mixed_case_findings = [
            {
                "title": "DENIAL OF SERVICE",
                "description": "RESOURCE EXHAUSTION POSSIBLE"
            },
            {
                "title": "Security Issue",
                "description": "ADD INPUT VALIDATION"
            },
            {
                "title": "Security Issue",
                "description": "HARDCODED PASSWORD DETECTED"
            }
        ]
        
        # First finding should be excluded (DOS)
        reason = HardExclusionRules.get_exclusion_reason(mixed_case_findings[0])
        assert reason is not None
        
        # Second finding should NOT be excluded (we removed generic validation patterns)
        reason = HardExclusionRules.get_exclusion_reason(mixed_case_findings[1])
        assert reason is None
        
        # Third finding should NOT be excluded (we removed secrets patterns)
        reason = HardExclusionRules.get_exclusion_reason(mixed_case_findings[2])
        assert reason is None
    
    def test_empty_finding_handling(self):
        """Test handling of empty or malformed findings."""
        empty_findings = [
            {},
            {"title": "", "description": ""},
            {"title": "Some title"},  # Missing description
            {"description": "Some description"},  # Missing title
            {"title": None, "description": None}
        ]
        
        for finding in empty_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is None  # Should not crash, just return None
    
    def test_combined_patterns(self):
        """Test findings that match multiple patterns."""
        finding = {
            "title": "DOS and validation issue",
            "description": "Missing rate limit leads to resource exhaustion"
        }
        
        reason = HardExclusionRules.get_exclusion_reason(finding)
        assert reason is not None
        # Should match at least one pattern (DOS or rate limiting)
    
    def test_regex_special_characters(self):
        """Test that regex special characters in findings don't cause issues."""
        findings_with_special_chars = [
            {
                "title": "Issue with $pecial ch@rs",
                "description": "Contains [brackets] and (parentheses)"
            },
            {
                "title": "Path: C:\\Windows\\System32",
                "description": "Backslashes \\ and dots ..."
            },
            {
                "title": "Regex chars: .* + ? ^ $ { } ( ) [ ] \\ |",
                "description": "All the special regex characters"
            }
        ]
        
        for finding in findings_with_special_chars:
            # Should not raise regex errors
            reason = HardExclusionRules.get_exclusion_reason(finding)
            # These don't match any patterns, so should return None
            assert reason is None
    
    def test_performance_with_long_text(self):
        """Test performance with very long descriptions."""
        long_text = "A" * 10000  # 10k characters
        finding = {
            "title": "Long finding",
            "description": long_text + " denial of service " + long_text
        }
        
        # Should handle long text efficiently
        reason = HardExclusionRules.get_exclusion_reason(finding)
        assert reason is not None  # Should find DOS pattern
        assert "DOS/resource exhaustion" in reason
    
    def test_memory_safety_exclusion_non_cpp_files(self):
        """Test that memory safety issues are excluded in non-C/C++ files."""
        memory_safety_findings = [
            {
                "title": "Buffer overflow vulnerability",
                "description": "Potential buffer overflow in string handling",
                "file": "app.py"
            },
            {
                "title": "Out of bounds access",
                "description": "Array out of bounds write detected",
                "file": "server.js"
            },
            {
                "title": "Memory corruption",
                "description": "Use after free vulnerability found",
                "file": "Main.java"
            },
            {
                "title": "Segmentation fault",
                "description": "Null pointer dereference causes segfault",
                "file": "handler.go"
            },
            {
                "title": "Integer overflow",
                "description": "Integer overflow in calculation",
                "file": "calc.rb"
            }
        ]
        
        for finding in memory_safety_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert "Memory safety finding in non-C/C++ code" in reason
    
    def test_memory_safety_not_excluded_cpp_files(self):
        """Test that memory safety issues are NOT excluded in C/C++ files."""
        cpp_memory_findings = [
            {
                "title": "Buffer overflow",
                "description": "Stack buffer overflow in strcpy",
                "file": "main.c"
            },
            {
                "title": "Out of bounds write",
                "description": "Array index out of bounds",
                "file": "parser.cc"
            },
            {
                "title": "Memory safety",
                "description": "Use after free in destructor",
                "file": "object.cpp"
            },
            {
                "title": "Bounds check missing",
                "description": "No bounds checking on user input",
                "file": "input.h"
            }
        ]
        
        for finding in cpp_memory_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is None  # Should NOT be excluded
    
    def test_memory_safety_exclusion_case_insensitive(self):
        """Test that file extension checking is case insensitive."""
        findings = [
            {
                "title": "Buffer overflow",
                "description": "Buffer overflow detected",
                "file": "App.PY"  # Uppercase extension
            },
            {
                "title": "Memory corruption",
                "description": "Memory corruption issue",
                "file": "SERVER.JS"  # All uppercase
            }
        ]
        
        for finding in findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert "Memory safety finding in non-C/C++ code" in reason
    
    def test_memory_safety_no_file_extension(self):
        """Test handling of files without extensions."""
        findings = [
            {
                "title": "Buffer overflow",
                "description": "Buffer overflow detected",
                "file": "Makefile"  # No extension
            },
            {
                "title": "Memory corruption",
                "description": "Memory corruption issue",
                "file": ""  # Empty file path
            }
        ]
        
        for finding in findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            # Should be excluded since they're not C/C++ files
            assert reason is not None
            assert "Memory safety finding in non-C/C++ code" in reason