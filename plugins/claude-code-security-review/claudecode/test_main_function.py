#!/usr/bin/env python3
"""
Unit tests for main function and full workflow.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch
from pathlib import Path

from claudecode.github_action_audit import main


class TestMainFunction:
    """Test main function execution flow."""
    
    def test_main_missing_environment_vars(self, capsys):
        """Test main with missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 2  # EXIT_CONFIGURATION_ERROR
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert 'error' in output
            assert 'GITHUB_REPOSITORY' in output['error']
    
    def test_main_missing_pr_number(self, capsys):
        """Test main with missing PR number."""
        with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'owner/repo'}, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 2  # EXIT_CONFIGURATION_ERROR
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert 'PR_NUMBER' in output['error']
    
    def test_main_invalid_pr_number(self, capsys):
        """Test main with invalid PR number."""
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': 'not-a-number'
        }, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 2  # EXIT_CONFIGURATION_ERROR
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert 'Invalid PR_NUMBER' in output['error']
    
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_main_github_client_init_failure(self, mock_client_class, capsys):
        """Test main when GitHub client initialization fails."""
        mock_client_class.side_effect = Exception("Token invalid")
        
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': '123',
            'GITHUB_TOKEN': 'invalid'
        }):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 2  # EXIT_CONFIGURATION_ERROR
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert 'Failed to initialize GitHub client' in output['error']
            assert 'Token invalid' in output['error']
    
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_main_claude_runner_init_failure(self, mock_client_class, mock_runner_class, capsys):
        """Test main when Claude runner initialization fails."""
        mock_client_class.return_value = Mock()
        mock_runner_class.side_effect = Exception("Runner error")
        
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': '123',
            'GITHUB_TOKEN': 'test-token'
        }):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 2  # EXIT_CONFIGURATION_ERROR
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert 'Failed to initialize Claude runner' in output['error']
    
    @patch('claudecode.github_action_audit.FindingsFilter')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_main_filter_initialization(self, mock_client_class, mock_runner_class, 
                                       mock_full_filter_class):
        """Test filter initialization logic."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_runner = Mock()
        mock_runner.validate_claude_available.return_value = (False, "Not available")
        mock_runner_class.return_value = mock_runner
        
        # Test with full filtering enabled
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': '123',
            'GITHUB_TOKEN': 'test-token',
            'ENABLE_CLAUDE_FILTERING': 'true',
            'ANTHROPIC_API_KEY': 'test-api-key'
        }):
            with pytest.raises(SystemExit):
                main()
            
            # Should initialize full filter
            mock_full_filter_class.assert_called_once()
            call_kwargs = mock_full_filter_class.call_args[1]
            assert call_kwargs['use_hard_exclusions'] is True
            assert call_kwargs['use_claude_filtering'] is True
            assert call_kwargs['api_key'] == 'test-api-key'
        
        # Reset mocks
        mock_full_filter_class.reset_mock()
        
        # Test with filtering disabled
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': '123',
            'GITHUB_TOKEN': 'test-token',
            'ENABLE_CLAUDE_FILTERING': 'false'
        }):
            with pytest.raises(SystemExit):
                main()
            
            # Should use FindingsFilter with hard exclusions only
            mock_full_filter_class.assert_called_once()
            call_kwargs = mock_full_filter_class.call_args[1]
            assert call_kwargs['use_hard_exclusions'] is True
            assert call_kwargs['use_claude_filtering'] is False
    
    @patch('claudecode.github_action_audit.FindingsFilter')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_main_claude_not_available(self, mock_client_class, mock_runner_class, 
                                      mock_filter_class, capsys):
        """Test when Claude is not available."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_runner = Mock()
        mock_runner.validate_claude_available.return_value = (False, "Claude not installed")
        mock_runner_class.return_value = mock_runner
        
        mock_filter_class.return_value = Mock()
        
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': '123',
            'GITHUB_TOKEN': 'test-token'
        }):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1  # Claude not available, exit 1
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert 'Claude Code not available' in output['error']
            assert 'Claude not installed' in output['error']
    
    @patch('claudecode.github_action_audit.get_security_audit_prompt')
    @patch('claudecode.github_action_audit.FindingsFilter')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_main_pr_data_fetch_failure(self, mock_client_class, mock_runner_class,
                                        mock_filter_class, mock_prompt_func, capsys):
        """Test when PR data fetch fails."""
        mock_client = Mock()
        mock_client.get_pr_data.side_effect = Exception("API error")
        mock_client_class.return_value = mock_client
        
        mock_runner = Mock()
        mock_runner.validate_claude_available.return_value = (True, "")
        mock_runner_class.return_value = mock_runner
        
        mock_filter_class.return_value = Mock()
        
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': '123',
            'GITHUB_TOKEN': 'test-token'
        }):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1  # API error, exit 1
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert 'Failed to fetch PR data' in output['error']
            assert 'API error' in output['error']
    
    @patch('pathlib.Path.cwd')
    @patch('claudecode.github_action_audit.get_security_audit_prompt')
    @patch('claudecode.github_action_audit.FindingsFilter')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_main_successful_audit_no_findings(self, mock_client_class, mock_runner_class,
                                               mock_filter_class, mock_prompt_func, 
                                               mock_cwd, capsys):
        """Test successful audit with no findings."""
        # Setup mocks
        mock_client = Mock()
        mock_client.get_pr_data.return_value = {
            'number': 123,
            'title': 'Test PR',
            'body': 'Description'
        }
        mock_client.get_pr_diff.return_value = "diff content"
        mock_client_class.return_value = mock_client
        
        mock_runner = Mock()
        mock_runner.validate_claude_available.return_value = (True, "")
        mock_runner.run_security_audit.return_value = (
            True, 
            "",
            {
                'findings': [],
                'analysis_summary': {
                    'files_reviewed': 5,
                    'high_severity': 0,
                    'medium_severity': 0,
                    'low_severity': 0
                }
            }
        )
        mock_runner_class.return_value = mock_runner
        
        mock_filter = Mock()
        mock_filter.filter_findings.return_value = (
            True,
            {
                'filtered_findings': [],
                'excluded_findings': [],
                'analysis_summary': {}
            },
            Mock()  # filter_stats
        )
        mock_filter_class.return_value = mock_filter
        
        mock_prompt_func.return_value = "security prompt"
        mock_cwd.return_value = Path('/tmp/repo')
        
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': '123',
            'GITHUB_TOKEN': 'test-token'
        }):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 0  # No findings, exit 0
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            
            assert output['pr_number'] == 123
            assert output['repo'] == 'owner/repo'
            assert len(output['findings']) == 0
            assert output['filtering_summary']['total_original_findings'] == 0
    
    @patch('pathlib.Path.cwd')
    @patch('claudecode.github_action_audit.get_security_audit_prompt')
    @patch('claudecode.github_action_audit.FindingsFilter')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_main_successful_audit_with_findings(self, mock_client_class, mock_runner_class,
                                                mock_filter_class, mock_prompt_func,
                                                mock_cwd, capsys):
        """Test successful audit with high severity findings."""
        # Setup mocks
        mock_client = Mock()
        mock_client.get_pr_data.return_value = {
            'number': 123,
            'title': 'Test PR',
            'body': 'Description'
        }
        mock_client.get_pr_diff.return_value = "diff content"
        mock_client._is_excluded.return_value = False  # Don't exclude any files in tests
        mock_client_class.return_value = mock_client
        
        findings = [
            {
                'file': 'test.py',
                'line': 10,
                'severity': 'HIGH',
                'description': 'SQL injection'
            },
            {
                'file': 'main.py',
                'line': 20,
                'severity': 'MEDIUM',
                'description': 'Weak crypto'
            }
        ]
        
        mock_runner = Mock()
        mock_runner.validate_claude_available.return_value = (True, "")
        mock_runner.run_security_audit.return_value = (
            True,
            "",
            {
                'findings': findings,
                'analysis_summary': {
                    'files_reviewed': 2,
                    'high_severity': 1,
                    'medium_severity': 1,
                    'low_severity': 0
                }
            }
        )
        mock_runner_class.return_value = mock_runner
        
        # Filter keeps only high severity
        mock_filter = Mock()
        mock_filter.filter_findings.return_value = (
            True,
            {
                'filtered_findings': [findings[0]],
                'excluded_findings': [findings[1]],
                'analysis_summary': {
                    'total_findings': 2,
                    'kept_findings': 1,
                    'excluded_findings': 1
                }
            },
            Mock()  # filter_stats
        )
        mock_filter_class.return_value = mock_filter
        
        mock_prompt_func.return_value = "security prompt"
        mock_cwd.return_value = Path('/tmp/repo')
        
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': '123',
            'GITHUB_TOKEN': 'test-token'
        }):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1  # High severity finding, exit 1
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            
            assert len(output['findings']) == 1
            assert output['findings'][0]['severity'] == 'HIGH'
            assert output['filtering_summary']['total_original_findings'] == 2
            assert output['filtering_summary']['excluded_findings'] == 1
            assert output['filtering_summary']['kept_findings'] == 1
    
    @patch('pathlib.Path.cwd')
    @patch('claudecode.github_action_audit.get_security_audit_prompt')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_main_with_full_filter(self, mock_client_class, mock_runner_class,
                                   mock_prompt_func, mock_cwd, capsys):
        """Test main with full FindingsFilter (LLM-based)."""
        # Setup mocks
        mock_client = Mock()
        mock_client.get_pr_data.return_value = {
            'number': 123,
            'title': 'Test PR',
            'body': 'Description'
        }
        mock_client.get_pr_diff.return_value = "diff content"
        mock_client._is_excluded.return_value = False  # Don't exclude any files in tests
        mock_client_class.return_value = mock_client
        
        findings = [{'file': 'test.py', 'line': 10, 'severity': 'HIGH', 'description': 'Issue'}]
        
        mock_runner = Mock()
        mock_runner.validate_claude_available.return_value = (True, "")
        mock_runner.run_security_audit.return_value = (True, "", {'findings': findings})
        mock_runner_class.return_value = mock_runner
        
        mock_prompt_func.return_value = "prompt"
        mock_cwd.return_value = Path('/tmp')
        
        # Mock FindingsFilter to return findings properly
        mock_filter = Mock()
        mock_filter.filter_findings.return_value = (
            True,
            {
                'filtered_findings': findings,
                'excluded_findings': [],
                'analysis_summary': {
                    'total_findings': 1,
                    'kept_findings': 1,
                    'excluded_findings': 0
                }
            },
            Mock()  # filter_stats
        )
        
        with patch('claudecode.github_action_audit.FindingsFilter', return_value=mock_filter):
            with patch.dict(os.environ, {
                'GITHUB_REPOSITORY': 'owner/repo',
                'PR_NUMBER': '123',
                'GITHUB_TOKEN': 'test-token',
                'ENABLE_CLAUDE_FILTERING': 'false',  # Use simple filter
            }):
                with pytest.raises(SystemExit):
                    main()
                
                captured = capsys.readouterr()
                output = json.loads(captured.out)
                
                # Check that we got successful results
                assert 'findings' in output
                assert len(output['findings']) == 1
                assert output['findings'][0]['severity'] == 'HIGH'
    
    @patch('pathlib.Path.cwd')
    @patch('claudecode.github_action_audit.get_security_audit_prompt')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_main_filter_failure_keeps_all_findings(self, mock_client_class, mock_runner_class,
                                                    mock_prompt_func, mock_cwd, capsys):
        """Test that filter failure keeps all findings with SimpleFindingsFilter."""
        # Setup mocks
        mock_client = Mock()
        mock_client.get_pr_data.return_value = {'number': 123, 'title': 'Test', 'body': ''}
        mock_client.get_pr_diff.return_value = "diff"
        mock_client._is_excluded.return_value = False  # Don't exclude any files in tests
        mock_client_class.return_value = mock_client
        
        findings = [
            {'file': 'a.py', 'line': 1, 'severity': 'HIGH', 'description': 'Issue 1'},
            {'file': 'b.py', 'line': 2, 'severity': 'HIGH', 'description': 'Issue 2'}
        ]
        
        mock_runner = Mock()
        mock_runner.validate_claude_available.return_value = (True, "")
        mock_runner.run_security_audit.return_value = (True, "", {'findings': findings})
        mock_runner_class.return_value = mock_runner
        
        mock_prompt_func.return_value = "prompt"
        mock_cwd.return_value = Path('/tmp')
        
        # Mock FindingsFilter to keep all findings
        mock_filter = Mock()
        mock_filter.filter_findings.return_value = (
            True,
            {
                'filtered_findings': findings,
                'excluded_findings': [],
                'analysis_summary': {
                    'total_findings': 2,
                    'kept_findings': 2,
                    'excluded_findings': 0
                }
            },
            Mock()  # filter_stats
        )
        
        with patch('claudecode.github_action_audit.FindingsFilter', return_value=mock_filter):
            with patch.dict(os.environ, {
                'GITHUB_REPOSITORY': 'owner/repo',
                'PR_NUMBER': '123',
                'GITHUB_TOKEN': 'test-token',
                'ENABLE_CLAUDE_FILTERING': 'false',  # Use simple filter
            }):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1  # Has HIGH findings
                
                captured = capsys.readouterr()
                output = json.loads(captured.out)
                
                # All findings should be kept
                assert len(output['findings']) == 2
    
    def test_main_unexpected_error(self, capsys):
        """Test unexpected error handling."""
        with patch('claudecode.github_action_audit.GitHubActionClient') as mock_class:
            mock_class.side_effect = Exception("Unexpected error!")
            
            with patch.dict(os.environ, {
                'GITHUB_REPOSITORY': 'owner/repo',
                'PR_NUMBER': '123',
                'GITHUB_TOKEN': 'test-token'
            }):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 2  # EXIT_CONFIGURATION_ERROR
                
                captured = capsys.readouterr()
                output = json.loads(captured.out)
                assert 'Unexpected error' in output['error']


class TestAuditFailureModes:
    """Test various audit failure scenarios."""
    
    @patch('pathlib.Path.cwd')
    @patch('claudecode.github_action_audit.get_security_audit_prompt')
    @patch('claudecode.github_action_audit.FindingsFilter')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    @patch('claudecode.github_action_audit.GitHubActionClient')
    def test_audit_failure(self, mock_client_class, mock_runner_class,
                          mock_filter_class, mock_prompt_func,
                          mock_cwd, capsys):
        """Test when security audit fails."""
        mock_client = Mock()
        mock_client.get_pr_data.return_value = {'number': 123}
        mock_client.get_pr_diff.return_value = "diff"
        mock_client_class.return_value = mock_client
        
        mock_runner = Mock()
        mock_runner.validate_claude_available.return_value = (True, "")
        mock_runner.run_security_audit.return_value = (
            False,
            "Claude execution failed",
            {}
        )
        mock_runner_class.return_value = mock_runner
        
        mock_filter_class.return_value = Mock()
        mock_prompt_func.return_value = "prompt"
        mock_cwd.return_value = Path('/tmp')
        
        with patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'owner/repo',
            'PR_NUMBER': '123',
            'GITHUB_TOKEN': 'test-token'
        }):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1  # Audit failure, exit 1
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert 'Security audit failed' in output['error']
            assert 'Claude execution failed' in output['error']
