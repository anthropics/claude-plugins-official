#!/usr/bin/env python3
"""
Pytest tests for SAST integration components.
"""

import pytest
import json

class TestClaudeCodeAudit:
    """Test the main audit functionality."""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up mock environment variables."""
        monkeypatch.setenv('GITHUB_REPOSITORY', 'test/repo')
        monkeypatch.setenv('PR_NUMBER', '123')
        monkeypatch.setenv('GITHUB_TOKEN', 'mock-token')
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'mock-api-key')
    
    def test_missing_environment_variables(self, monkeypatch, capsys):
        """Test behavior with missing environment variables."""
        from claudecode import github_action_audit
        
        # Test missing GITHUB_REPOSITORY
        monkeypatch.delenv('GITHUB_REPOSITORY', raising=False)
        with pytest.raises(SystemExit) as exc_info:
            github_action_audit.main()
        assert exc_info.value.code == 2  # EXIT_CONFIGURATION_ERROR
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert 'GITHUB_REPOSITORY' in output['error']
        
        # Test missing PR_NUMBER
        monkeypatch.setenv('GITHUB_REPOSITORY', 'test/repo')
        monkeypatch.delenv('PR_NUMBER', raising=False)
        with pytest.raises(SystemExit) as exc_info:
            github_action_audit.main()
        assert exc_info.value.code == 2  # EXIT_CONFIGURATION_ERROR
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert 'PR_NUMBER' in output['error']
    
    def test_invalid_pr_number(self, monkeypatch, capsys):
        """Test behavior with invalid PR number."""
        from claudecode  import github_action_audit
        
        monkeypatch.setenv('GITHUB_REPOSITORY', 'test/repo')
        monkeypatch.setenv('PR_NUMBER', 'invalid')
        monkeypatch.setenv('GITHUB_TOKEN', 'mock-token')
        
        with pytest.raises(SystemExit) as exc_info:
            github_action_audit.main()
        assert exc_info.value.code == 2  # EXIT_CONFIGURATION_ERROR
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert 'Invalid PR_NUMBER' in output['error']


class TestEnvironmentSetup:
    """Test environment setup and configuration."""
    
    def test_anthropic_api_key_handling(self, monkeypatch):
        """Test handling of Anthropic API key."""
        from claudecode.github_action_audit import SimpleClaudeRunner
        
        runner = SimpleClaudeRunner()
        
        # Test with API key set
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')
        valid, error = runner.validate_claude_available()
        # Note: This will fail if claude CLI is not installed, which is OK
        if not valid and 'not installed' in error:
            pytest.fail("Claude CLI not installed")
        
        # Test without API key
        monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
        valid, error = runner.validate_claude_available()
        if 'not installed' not in error:
            assert not valid
            assert 'ANTHROPIC_API_KEY' in error


class TestFilteringIntegration:
    """Test the filtering system integration."""
    
    def test_full_filter_with_llm_disabled(self):
        """Test FindingsFilter with LLM filtering disabled."""
        from claudecode.findings_filter import FindingsFilter
        
        # Create filter with LLM disabled
        filter_instance = FindingsFilter(
            use_hard_exclusions=True,
            use_claude_filtering=False
        )
        
        test_findings = [
            {'description': 'SQL injection vulnerability', 'severity': 'HIGH'},
            {'description': 'Missing rate limiting', 'severity': 'MEDIUM'},
        ]
        
        success, results, stats = filter_instance.filter_findings(test_findings)
        
        assert success is True
        assert stats.total_findings == 2
        assert stats.kept_findings == 1  # Only SQL injection
        assert stats.hard_excluded == 1  # Rate limiting
        assert stats.claude_excluded == 0  # No Claude filtering
    