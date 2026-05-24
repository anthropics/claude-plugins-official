"""Unit tests for helper functions in github_action_audit module."""

import pytest
import os
from unittest.mock import patch, MagicMock


from claudecode.github_action_audit import (
    get_environment_config,
    initialize_clients,
    initialize_findings_filter,
    run_security_audit,
    apply_findings_filter,
    ConfigurationError,
    AuditError
)
from claudecode.findings_filter import FindingsFilter


class TestHelperFunctions:
    """Test helper functions in github_action_audit module."""
    
    def test_get_environment_config_success(self):
        """Test successful environment configuration retrieval."""
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': '123'
        }):
            repo_name, pr_number = get_environment_config()
            
            assert repo_name == 'owner/repo'
            assert pr_number == 123
    
    def test_get_environment_config_missing_repository(self):
        """Test error when GITHUB_REPOSITORY is missing."""
        with patch.dict(os.environ, {'PR_NUMBER': '123'}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                get_environment_config()
            
            assert "GITHUB_REPOSITORY environment variable required" in str(exc_info.value)
    
    def test_get_environment_config_missing_pr_number(self):
        """Test error when PR_NUMBER is missing."""
        with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'owner/repo'}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                get_environment_config()
            
            assert "PR_NUMBER environment variable required" in str(exc_info.value)
    
    def test_get_environment_config_invalid_pr_number(self):
        """Test error when PR_NUMBER is not a valid integer."""
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': 'not-a-number'
        }):
            with pytest.raises(ConfigurationError) as exc_info:
                get_environment_config()
            
            assert "Invalid PR_NUMBER" in str(exc_info.value)
    
    @patch('claudecode.github_action_audit.GitHubActionClient')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    def test_initialize_clients_success(self, mock_claude_runner, mock_github_client):
        """Test successful client initialization."""
        mock_github_instance = MagicMock()
        mock_claude_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        mock_claude_runner.return_value = mock_claude_instance
        
        github_client, claude_runner = initialize_clients()
        
        assert github_client == mock_github_instance
        assert claude_runner == mock_claude_instance
        mock_github_client.assert_called_once()
        mock_claude_runner.assert_called_once()
    
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_initialize_clients_github_failure(self, mock_github_client):
        """Test error when GitHub client initialization fails."""
        mock_github_client.side_effect = Exception("GitHub API error")
        
        with pytest.raises(ConfigurationError) as exc_info:
            initialize_clients()
        
        assert "Failed to initialize GitHub client" in str(exc_info.value)
        assert "GitHub API error" in str(exc_info.value)
    
    @patch('claudecode.github_action_audit.GitHubActionClient')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    def test_initialize_clients_claude_failure(self, mock_claude_runner, mock_github_client):
        """Test error when Claude runner initialization fails."""
        mock_github_client.return_value = MagicMock()
        mock_claude_runner.side_effect = Exception("Claude init error")
        
        with pytest.raises(ConfigurationError) as exc_info:
            initialize_clients()
        
        assert "Failed to initialize Claude runner" in str(exc_info.value)
        assert "Claude init error" in str(exc_info.value)
    
    @patch('claudecode.github_action_audit.FindingsFilter')
    def test_initialize_findings_filter_with_claude(self, mock_filter):
        """Test initializing findings filter with Claude API enabled."""
        mock_filter_instance = MagicMock()
        mock_filter.return_value = mock_filter_instance
        
        with patch.dict(os.environ, {
            'ENABLE_CLAUDE_FILTERING': 'true',
            'ANTHROPIC_API_KEY': 'test-key-123'
        }):
            result = initialize_findings_filter()
            
            assert result == mock_filter_instance
            mock_filter.assert_called_once_with(
                use_hard_exclusions=True,
                use_claude_filtering=True,
                api_key='test-key-123',
                custom_filtering_instructions=None
            )
    
    @patch('claudecode.github_action_audit.FindingsFilter')
    def test_initialize_findings_filter_without_claude(self, mock_simple_filter):
        """Test initializing findings filter without Claude API."""
        mock_filter_instance = MagicMock()
        mock_simple_filter.return_value = mock_filter_instance
        
        with patch.dict(os.environ, {
            'ENABLE_CLAUDE_FILTERING': 'false'
        }, clear=True):
            result = initialize_findings_filter()
            
            assert result == mock_filter_instance
            mock_simple_filter.assert_called_once()
    
    @patch('claudecode.github_action_audit.FindingsFilter')
    def test_initialize_findings_filter_with_defaults(self, mock_simple_filter):
        """Test initializing findings filter with defaults."""
        mock_filter_instance = MagicMock()
        mock_simple_filter.return_value = mock_filter_instance
        
        with patch.dict(os.environ, {}, clear=True):
            result = initialize_findings_filter()
            
            assert result == mock_filter_instance
    
    def test_run_security_audit_success(self):
        """Test successful security audit execution."""
        mock_runner = MagicMock()
        mock_runner.run_security_audit.return_value = (
            True,
            "",
            {"findings": [{"id": 1}], "analysis_summary": {}}
        )
        
        result = run_security_audit(mock_runner, "test prompt")
        
        assert result == {"findings": [{"id": 1}], "analysis_summary": {}}
        mock_runner.run_security_audit.assert_called_once()
    
    def test_run_security_audit_failure(self):
        """Test security audit execution failure."""
        mock_runner = MagicMock()
        mock_runner.run_security_audit.return_value = (
            False,
            "Audit failed: timeout",
            {}
        )
        
        with pytest.raises(AuditError) as exc_info:
            run_security_audit(mock_runner, "test prompt")
        
        assert "Security audit failed: Audit failed: timeout" in str(exc_info.value)
    
    def test_apply_findings_filter_with_findings_filter(self):
        """Test applying FindingsFilter to findings."""
        mock_filter = MagicMock(spec=FindingsFilter)
        mock_filter.filter_findings.return_value = (
            True,
            {
                'filtered_findings': [{"id": 1}],
                'excluded_findings': [{"id": 2}],
                'analysis_summary': {'total': 2, 'kept': 1}
            },
            MagicMock()  # filter_stats
        )
        
        original_findings = [{"id": 1}, {"id": 2}]
        pr_context = {"repo_name": "test/repo"}
        
        # Create mock github client
        mock_github_client = MagicMock()
        mock_github_client._is_excluded.return_value = False
        
        kept, excluded, summary = apply_findings_filter(
            mock_filter, original_findings, pr_context, mock_github_client
        )
        
        assert kept == [{"id": 1}]
        assert excluded == [{"id": 2}]
        assert summary == {'total': 2, 'kept': 1, 'directory_excluded_count': 0}
        
        mock_filter.filter_findings.assert_called_once_with(original_findings, pr_context)
    
    def test_apply_findings_filter_with_simple_filter(self):
        """Test applying FindingsFilter to findings."""
        mock_filter = MagicMock(spec=FindingsFilter)
        mock_filter.filter_findings.return_value = (
            True,
            {
                'filtered_findings': [{"id": 1}],
                'excluded_findings': [{"id": 2}],
                'analysis_summary': {}
            },
            MagicMock()  # filter_stats
        )
        
        original_findings = [{"id": 1}, {"id": 2}]
        pr_context = {"repo_name": "test/repo"}
        
        # Create mock github client
        mock_github_client = MagicMock()
        mock_github_client._is_excluded.return_value = False
        
        kept, excluded, summary = apply_findings_filter(
            mock_filter, original_findings, pr_context, mock_github_client
        )
        
        assert kept == [{"id": 1}]
        assert excluded == [{"id": 2}]
        assert summary == {'directory_excluded_count': 0}
        
        mock_filter.filter_findings.assert_called_once_with(original_findings, pr_context)
    
    def test_apply_findings_filter_failure(self):
        """Test handling of filter failure."""
        mock_filter = MagicMock(spec=FindingsFilter)
        mock_filter.filter_findings.return_value = (
            False,  # filter failed
            {},
            MagicMock()
        )
        
        original_findings = [{"id": 1}, {"id": 2}]
        pr_context = {"repo_name": "test/repo"}
        
        # Create mock github client
        mock_github_client = MagicMock()
        mock_github_client._is_excluded.return_value = False
        
        kept, excluded, summary = apply_findings_filter(
            mock_filter, original_findings, pr_context, mock_github_client
        )
        
        # On failure, should keep all findings
        assert kept == original_findings
        assert excluded == []
        assert summary == {'directory_excluded_count': 0}