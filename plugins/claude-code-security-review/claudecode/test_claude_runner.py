#!/usr/bin/env python3
"""
Unit tests for SimpleClaudeRunner.
"""

import json
import os
import subprocess
from unittest.mock import Mock, patch
from pathlib import Path

from claudecode.github_action_audit import SimpleClaudeRunner
from claudecode.constants import DEFAULT_CLAUDE_MODEL


class TestSimpleClaudeRunner:
    """Test SimpleClaudeRunner functionality."""
    
    def test_init(self):
        """Test runner initialization."""
        runner = SimpleClaudeRunner(timeout_minutes=30)
        assert runner.timeout_seconds == 1800
        
        runner2 = SimpleClaudeRunner()  # Default
        assert runner2.timeout_seconds == 1200  # 20 minutes default
    
    @patch('subprocess.run')
    def test_validate_claude_available_success(self, mock_run):
        """Test successful Claude validation."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='claude version 1.0.0',
            stderr=''
        )
        
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            runner = SimpleClaudeRunner()
            success, error = runner.validate_claude_available()
        
        assert success is True
        assert error == ''
        mock_run.assert_called_once_with(
            ['claude', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
    
    @patch('subprocess.run')
    def test_validate_claude_available_no_api_key(self, mock_run):
        """Test Claude validation without API key."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='claude version 1.0.0',
            stderr=''
        )
        
        # Remove API key
        env = os.environ.copy()
        env.pop('ANTHROPIC_API_KEY', None)
        
        with patch.dict(os.environ, env, clear=True):
            runner = SimpleClaudeRunner()
            success, error = runner.validate_claude_available()
        
        assert success is False
        assert 'ANTHROPIC_API_KEY environment variable is not set' in error
    
    @patch('subprocess.run')
    def test_validate_claude_available_not_installed(self, mock_run):
        """Test Claude validation when not installed."""
        mock_run.side_effect = FileNotFoundError()
        
        runner = SimpleClaudeRunner()
        success, error = runner.validate_claude_available()
        
        assert success is False
        assert 'Claude Code is not installed or not in PATH' in error
    
    @patch('subprocess.run')
    def test_validate_claude_available_error(self, mock_run):
        """Test Claude validation with error."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout='',
            stderr='Error: Authentication failed'
        )
        
        runner = SimpleClaudeRunner()
        success, error = runner.validate_claude_available()
        
        assert success is False
        assert 'exit code 1' in error
        assert 'Authentication failed' in error
    
    @patch('subprocess.run')
    def test_validate_claude_available_timeout(self, mock_run):
        """Test Claude validation timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(['claude'], 10)
        
        runner = SimpleClaudeRunner()
        success, error = runner.validate_claude_available()
        
        assert success is False
        assert 'timed out' in error
    
    def test_run_security_audit_missing_directory(self):
        """Test audit with missing directory."""
        runner = SimpleClaudeRunner()
        success, error, results = runner.run_security_audit(
            Path('/non/existent/path'),
            "test prompt"
        )
        
        assert success is False
        assert 'Repository directory does not exist' in error
        assert results == {}
    
    @patch('subprocess.run')
    def test_run_security_audit_success(self, mock_run):
        """Test successful security audit."""
        # Claude Code returns wrapped format with 'result' field
        findings_data = {
            "findings": [
                {
                    "file": "test.py",
                    "line": 10,
                    "severity": "HIGH",
                    "description": "SQL injection vulnerability"
                }
            ],
            "analysis_summary": {
                "files_reviewed": 5,
                "high_severity": 1,
                "medium_severity": 0,
                "low_severity": 0,
                "review_completed": True
            }
        }
        
        audit_result = {
            "result": json.dumps(findings_data)
        }
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(audit_result),
            stderr=''
        )
        
        runner = SimpleClaudeRunner()
        with patch('pathlib.Path.exists', return_value=True):
            success, error, results = runner.run_security_audit(
                Path('/tmp/test'),
                "test prompt"
            )
        
        assert success is True
        assert error == ''
        assert len(results['findings']) == 1
        assert results['findings'][0]['severity'] == 'HIGH'
        
        # Verify subprocess call
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == [
            'claude',
            '--output-format', 'json',
            '--model', DEFAULT_CLAUDE_MODEL,
            '--disallowed-tools', 'Bash(ps:*)'
        ]
        assert call_args[1]['input'] == 'test prompt'
        assert call_args[1]['cwd'] == Path('/tmp/test')
    
    @patch('subprocess.run')
    def test_run_security_audit_large_prompt_warning(self, mock_run, capsys):
        """Test warning for large prompts."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"findings": []}',
            stderr=''
        )
        
        # Create a prompt larger than 1MB
        large_prompt = 'x' * (1024 * 1024 + 1000)
        
        runner = SimpleClaudeRunner()
        with patch('pathlib.Path.exists', return_value=True):
            success, error, results = runner.run_security_audit(
                Path('/tmp/test'),
                large_prompt
            )
        
        captured = capsys.readouterr()
        assert '[Warning] Large prompt size' in captured.err
        assert success is True
    
    @patch('subprocess.run')
    def test_run_security_audit_retry_on_failure(self, mock_run):
        """Test retry logic on failure."""
        # First call fails, second succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stdout='', stderr='Temporary error'),
            Mock(returncode=0, stdout='{"findings": []}', stderr='')
        ]
        
        runner = SimpleClaudeRunner()
        with patch('pathlib.Path.exists', return_value=True):
            success, error, results = runner.run_security_audit(
                Path('/tmp/test'),
                "test prompt"
            )
        
        assert success is True
        assert error == ''
        assert mock_run.call_count == 2  # Retried once
    
    @patch('subprocess.run')
    def test_run_security_audit_retry_on_error_during_execution(self, mock_run):
        """Test retry on error_during_execution result."""
        error_result = {
            "type": "result",
            "subtype": "error_during_execution",
            "error": "Temporary execution error"
        }
        
        success_result = {
            "result": json.dumps({
                "findings": [{"file": "test.py", "line": 1, "severity": "LOW", "description": "Issue"}],
                "analysis_summary": {
                    "files_reviewed": 1,
                    "high_severity": 0,
                    "medium_severity": 0,
                    "low_severity": 1,
                    "review_completed": True
                }
            })
        }
        
        mock_run.side_effect = [
            Mock(returncode=0, stdout=json.dumps(error_result), stderr=''),
            Mock(returncode=0, stdout=json.dumps(success_result), stderr='')
        ]
        
        runner = SimpleClaudeRunner()
        with patch('pathlib.Path.exists', return_value=True):
            success, error, results = runner.run_security_audit(
                Path('/tmp/test'),
                "test prompt"
            )
        
        assert success is True
        assert len(results['findings']) == 1
        assert mock_run.call_count == 2
    
    @patch('subprocess.run')
    def test_run_security_audit_timeout(self, mock_run):
        """Test timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(['claude'], 1200)
        
        runner = SimpleClaudeRunner()
        with patch('pathlib.Path.exists', return_value=True):
            success, error, results = runner.run_security_audit(
                Path('/tmp/test'),
                "test prompt"
            )
        
        assert success is False
        assert 'timed out after 20 minutes' in error
        assert results == {}
    
    @patch('subprocess.run')
    def test_run_security_audit_json_parse_failure_with_retry(self, mock_run):
        """Test JSON parse failure with retry."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout='Invalid JSON', stderr=''),
            Mock(returncode=0, stdout='Still invalid', stderr='')
        ]
        
        runner = SimpleClaudeRunner()
        with patch('pathlib.Path.exists', return_value=True):
            success, error, results = runner.run_security_audit(
                Path('/tmp/test'),
                "test prompt"
            )
        
        assert success is False
        assert 'Failed to parse Claude output' in error
        assert mock_run.call_count == 2
    
    def test_extract_security_findings_claude_wrapper(self):
        """Test extraction from Claude Code wrapper format."""
        runner = SimpleClaudeRunner()
        
        # Test with result field containing JSON string
        claude_output = {
            "result": json.dumps({
                "findings": [
                    {"file": "test.py", "line": 10, "severity": "HIGH"}
                ]
            })
        }
        
        result = runner._extract_security_findings(claude_output)
        assert len(result['findings']) == 1
        assert result['findings'][0]['file'] == 'test.py'
    
    def test_extract_security_findings_direct_format(self):
        """Test that direct findings format was removed - only wrapped format is supported."""
        runner = SimpleClaudeRunner()
        
        # Direct format (without 'result' wrapper) should return empty
        claude_output = {
            "findings": [
                {"file": "main.py", "line": 20, "severity": "MEDIUM"}
            ],
            "analysis_summary": {
                "files_reviewed": 3,
                "high_severity": 0,
                "medium_severity": 1,
                "low_severity": 0
            }
        }
        
        result = runner._extract_security_findings(claude_output)
        # Should return empty structure since direct format is not supported
        assert len(result['findings']) == 0
        assert result['analysis_summary']['review_completed'] is False
    
    def test_extract_security_findings_text_fallback(self):
        """Test that text fallback was removed - only JSON is supported."""
        runner = SimpleClaudeRunner()
        
        # Test with result containing text (not JSON)
        claude_output = {
            "result": "Found SQL injection vulnerability in database.py line 45"
        }
        
        # Should return empty findings since we don't parse text anymore
        result = runner._extract_security_findings(claude_output)
        assert len(result['findings']) == 0
        assert result['analysis_summary']['review_completed'] is False
    
    def test_extract_security_findings_empty(self):
        """Test extraction with no findings."""
        runner = SimpleClaudeRunner()
        
        # Various empty formats
        for output in [None, {}, {"result": ""}, {"other": "data"}]:
            result = runner._extract_security_findings(output)
            assert result['findings'] == []
            assert result['analysis_summary']['review_completed'] is False
    
    def test_create_findings_from_text(self):
        """Test that _create_findings_from_text was removed."""
        runner = SimpleClaudeRunner()
        
        # Method should not exist
        assert not hasattr(runner, '_create_findings_from_text')
    
    def test_create_findings_from_text_no_issues(self):
        """Test that _create_findings_from_text was removed."""
        runner = SimpleClaudeRunner()
        
        # Method should not exist
        assert not hasattr(runner, '_create_findings_from_text')


class TestClaudeRunnerEdgeCases:
    """Test edge cases and error scenarios."""
    
    @patch('subprocess.run')
    def test_claude_output_formats(self, mock_run):
        """Test various Claude output formats."""
        runner = SimpleClaudeRunner()
        
        # Test nested JSON in result - result field should be string
        nested_output = {
            "type": "result",
            "result": json.dumps({
                "findings": [
                    {"file": "test.py", "line": 1, "severity": "HIGH", "description": "Issue"}
                ]
            })
        }
        
        with patch('pathlib.Path.exists', return_value=True):
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps(nested_output),
                stderr=''
            )
            
            success, error, results = runner.run_security_audit(
                Path('/tmp/test'),
                "test"
            )
        
        # Should extract findings from nested structure
        assert success is True
        assert len(results['findings']) == 1
    
    @patch('subprocess.run')
    def test_partial_json_recovery(self, mock_run):
        """Test recovery from partial JSON output."""
        # Simulate truncated JSON
        partial_json = '{"findings": [{"file": "test.py", "line": 10, "sev'
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout=partial_json,
            stderr=''
        )
        
        runner = SimpleClaudeRunner()
        with patch('pathlib.Path.exists', return_value=True):
            success, error, results = runner.run_security_audit(
                Path('/tmp/test'),
                "test"
            )
        
        # Should fail to parse and retry
        assert mock_run.call_count == 2
    
    @patch('subprocess.run')
    def test_exception_handling(self, mock_run):
        """Test general exception handling."""
        mock_run.side_effect = Exception("Unexpected error")
        
        runner = SimpleClaudeRunner()
        with patch('pathlib.Path.exists', return_value=True):
            success, error, results = runner.run_security_audit(
                Path('/tmp/test'),
                "test"
            )
        
        assert success is False
        assert 'Unexpected error' in error
        assert results == {}
