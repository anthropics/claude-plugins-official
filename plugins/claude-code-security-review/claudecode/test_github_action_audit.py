#!/usr/bin/env python3
"""
Pytest tests for GitHub Action audit script components.
"""


class TestImports:
    """Test that all required modules can be imported."""
    
    def test_main_module_import(self):
        """Test that the main module can be imported."""
        from claudecode import github_action_audit
        assert hasattr(github_action_audit, 'GitHubActionClient')
        assert hasattr(github_action_audit, 'SimpleClaudeRunner')
        # SimpleFindingsFilter was removed
        assert hasattr(github_action_audit, 'main')
    
    def test_component_imports(self):
        """Test that all component modules can be imported."""
        from claudecode.prompts import get_security_audit_prompt
        from claudecode.json_parser import parse_json_with_fallbacks, extract_json_from_text
        
        # Verify they're callable/usable
        assert callable(get_security_audit_prompt)
        assert callable(parse_json_with_fallbacks)
        assert callable(extract_json_from_text)


class TestHardExclusionRules:
    """Test the HardExclusionRules patterns."""
    
    def test_dos_patterns(self):
        """Test DOS pattern exclusions."""
        from claudecode.findings_filter import HardExclusionRules
        
        dos_findings = [
            {'description': 'Potential denial of service vulnerability'},
            {'description': 'DOS attack through resource exhaustion'},
            {'description': 'Infinite loop causing resource exhaustion'},
        ]
        
        for finding in dos_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert 'dos' in reason.lower()
    
    def test_rate_limiting_patterns(self):
        """Test rate limiting pattern exclusions."""
        from claudecode.findings_filter import HardExclusionRules
        
        rate_limit_findings = [
            {'description': 'Missing rate limiting on endpoint'},
            {'description': 'No rate limit implemented for API'},
            {'description': 'Implement rate limiting for this route'},
        ]
        
        for finding in rate_limit_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert 'rate limit' in reason.lower()
    
    def test_open_redirect_patterns(self):
        """Test open redirect pattern exclusions."""
        from claudecode.findings_filter import HardExclusionRules
        
        redirect_findings = [
            {'description': 'Open redirect vulnerability found'},
            {'description': 'Unvalidated redirect in URL parameter'},
            {'description': 'Redirect attack possible through user input'},
        ]
        
        for finding in redirect_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert 'open redirect' in reason.lower()
    
    def test_markdown_file_exclusion(self):
        """Test that findings in .md files are excluded."""
        from claudecode.findings_filter import HardExclusionRules
        
        md_findings = [
            {'file': 'README.md', 'description': 'SQL injection vulnerability'},
            {'file': 'docs/security.md', 'description': 'Command injection found'},
            {'file': 'CHANGELOG.MD', 'description': 'XSS vulnerability'},  # Test case insensitive
            {'file': 'path/to/file.Md', 'description': 'Path traversal'},  # Mixed case
        ]
        
        for finding in md_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is not None
            assert 'markdown' in reason.lower()
    
    def test_non_markdown_files_not_excluded(self):
        """Test that findings in non-.md files are not excluded due to file extension."""
        from claudecode.findings_filter import HardExclusionRules
        
        non_md_findings = [
            {'file': 'main.py', 'description': 'SQL injection vulnerability'},
            {'file': 'server.js', 'description': 'Command injection found'},
            {'file': 'index.html', 'description': 'XSS vulnerability'},
            {'file': 'config.yml', 'description': 'Hardcoded credentials'},
            {'file': 'README.txt', 'description': 'Path traversal'},
            {'file': 'file.mdx', 'description': 'Security issue'},  # Not .md
        ]
        
        for finding in non_md_findings:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            # Should not be excluded for being a markdown file
            # (might be excluded for other reasons like DOS patterns)
            if reason:
                assert 'markdown' not in reason.lower()
    
    def test_keeps_real_vulnerabilities(self):
        """Test that real vulnerabilities are not excluded."""
        from claudecode.findings_filter import HardExclusionRules
        
        real_vulns = [
            {'file': 'auth.py', 'description': 'SQL injection in user authentication'},
            {'file': 'exec.js', 'description': 'Command injection through user input'},
            {'file': 'comments.php', 'description': 'Cross-site scripting in comment field'},
            {'file': 'upload.go', 'description': 'Path traversal in file upload'},
        ]
        
        for finding in real_vulns:
            reason = HardExclusionRules.get_exclusion_reason(finding)
            assert reason is None


class TestJSONParser:
    """Test JSON parsing utilities."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        from claudecode.json_parser import parse_json_with_fallbacks
        
        valid_json = '{"test": "data", "number": 123}'
        success, result = parse_json_with_fallbacks(valid_json, "test")
        
        assert success is True
        assert result == {"test": "data", "number": 123}
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        from claudecode.json_parser import parse_json_with_fallbacks
        
        invalid_json = '{invalid json}'
        success, result = parse_json_with_fallbacks(invalid_json, "test")
        
        assert success is False
        assert 'error' in result
        assert 'Invalid JSON response' in result['error']
    
    def test_extract_json_from_text(self):
        """Test extracting JSON from mixed text."""
        from claudecode.json_parser import extract_json_from_text
        
        mixed_text = 'Some text before {"key": "value"} some text after'
        result = extract_json_from_text(mixed_text)
        
        assert result == {"key": "value"}
    
    def test_extract_json_from_text_no_json(self):
        """Test extracting JSON when none exists."""
        from claudecode.json_parser import extract_json_from_text
        
        plain_text = 'This is just plain text with no JSON'
        result = extract_json_from_text(plain_text)
        
        assert result is None


class TestPromptsModule:
    """Test the prompts module."""
    
    def test_get_security_audit_prompt(self):
        """Test security audit prompt generation."""
        from claudecode.prompts import get_security_audit_prompt
        
        pr_data = {
            'number': 123,
            'title': 'Test PR',
            'body': 'Test description',
            'user': 'testuser',
            'changed_files': 1,
            'additions': 10,
            'deletions': 5,
            'head': {
                'repo': {
                    'full_name': 'owner/repo'
                }
            },
            'files': [
                {
                    'filename': 'test.py',
                    'status': 'modified',
                    'additions': 10,
                    'deletions': 5,
                    'patch': '@@ -1,5 +1,10 @@\n+added line'
                }
            ]
        }
        
        pr_diff = "diff --git a/test.py b/test.py\n+added line"
        
        prompt = get_security_audit_prompt(pr_data, pr_diff)
        
        assert isinstance(prompt, str)
        assert 'security' in prompt.lower()
        assert 'PR #123' in prompt
        assert 'test.py' in prompt


class TestDeploymentPRDetection:
    """Test deployment PR title pattern matching."""
    
    def test_deployment_pr_patterns(self):
        """Test that deployment PR titles are correctly identified."""
        import re
        
        deployment_pattern = r'^Deploy\s+[a-f0-9]{6,}\s+to\s+(production|staging|development|production-services)'
        
        # These should match
        deployment_titles = [
            "Deploy 53f395b0 to production-services",
            "Deploy af179b5b to production",
            "Deploy 1a3cb909 to production",
            "Deploy 49c09ea5 to production-services",
            "Deploy 8e7acc60 to production",
            "Deploy e0b1fe0b to production-services",
            "Deploy c53e6010 to production",
            "Deploy 42c4a061 to production",
            "Deploy 9de55976 to production-services",
            "deploy abcdef123456 to staging",  # lowercase should work
            "DEPLOY ABCDEF01 TO DEVELOPMENT",  # uppercase should work
        ]
        
        for title in deployment_titles:
            assert re.match(deployment_pattern, title, re.IGNORECASE), f"Failed to match deployment PR: {title}"
    
    def test_non_deployment_pr_patterns(self):
        """Test that non-deployment PR titles are not matched."""
        import re
        
        deployment_pattern = r'^Deploy\s+[a-f0-9]{6,}\s+to\s+(production|staging|development|production-services)'
        
        # These should NOT match
        non_deployment_titles = [
            "Add new feature",
            "Fix bug in deployment script",
            "Update deployment documentation",
            "Deploy new feature to production",  # No commit hash
            "Deploy abc to production",  # Too short hash
            "Deploy 12345g to production",  # Non-hex character
            "Preparing deploy af179b5b to production",  # Doesn't start with Deploy
            "Deploy af179b5b to testing",  # Wrong environment
            "Deploy af179b5b",  # Missing environment
            "af179b5b to production",  # Missing Deploy prefix
        ]
        
        for title in non_deployment_titles:
            assert not re.match(deployment_pattern, title, re.IGNORECASE), f"Incorrectly matched non-deployment PR: {title}"

