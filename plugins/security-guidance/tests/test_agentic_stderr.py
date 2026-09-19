import io
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add hooks directory to sys.path so we can import plugin modules
HOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hooks"))
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import llm


class TestAgenticStderrRegression(unittest.TestCase):
    """Regression tests for issue #92987:
    Verify that agentic review supplies a callable stderr handler to ClaudeAgentOptions,
    capturing child stderr so inner CLI warnings do not leak into the parent hook's
    sys.stderr or replace the review findings.
    """

    def test_agentic_review_captures_child_stderr_and_preserves_findings(self):
        """Simulate inner CLI emitting warning to stderr; verify child stderr does not leak
        into parent sys.stderr and review findings remain fully intact."""
        captured_options = []

        class MockClaudeAgentOptions:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                self.stderr = kwargs.get("stderr")
                captured_options.append(self)

        class MockAssistantMessage:
            pass

        class MockResultMessage:
            def __init__(self):
                self.subtype = "success"
                self.structured_output = {
                    "findings": [
                        {
                            "category": "hardcoded_secret",
                            "filePath": "src/auth.ts",
                            "severity": "high",
                            "vulnerableCode": "const API_KEY = 'secret';",
                            "description": "Hardcoded API key in source file",
                        }
                    ]
                }
                self.usage = {"input_tokens": 120, "output_tokens": 60}
                self.total_cost_usd = 0.002

        warning_line = (
            "⚠ claude.ai connectors are disabled because ANTHROPIC_API_KEY or another auth source is set\n"
        )

        async def mock_query(prompt, options):
            # When options.stderr is provided, the SDK pipes child stderr to that callback.
            # When options.stderr is None (the bug), the child process inherits sys.stderr,
            # leaking warning lines straight into the hook's stderr!
            if options.stderr and callable(options.stderr):
                options.stderr(warning_line)
            else:
                sys.stderr.write(warning_line)
            yield MockResultMessage()

        mock_sdk = MagicMock()
        mock_sdk.ClaudeAgentOptions = MockClaudeAgentOptions
        mock_sdk.AssistantMessage = MockAssistantMessage
        mock_sdk.ResultMessage = MockResultMessage
        mock_sdk.query = mock_query

        with patch.dict(sys.modules, {"claude_agent_sdk": mock_sdk}), \
             patch("llm.debug_log") as mock_debug_log, \
             patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:

            guidance, vulns, metrics = llm.agentic_review(
                repo_dir=".",
                diff_files=[("src/auth.ts", "+const API_KEY = 'secret';")],
                touched_paths=["src/auth.ts"],
            )

            # 1. Verify ClaudeAgentOptions was instantiated
            self.assertTrue(len(captured_options) >= 1, "Expected at least one ClaudeAgentOptions call")

            # 2. Verify opts.stderr is NOT None and is callable
            opts = captured_options[0]
            self.assertIsNotNone(opts.stderr, "opts.stderr must not be None (Issue #92987)")
            self.assertTrue(callable(opts.stderr), "opts.stderr must be a callable handler")

            # 3. Verify that child stderr did NOT leak into the parent process's sys.stderr
            stderr_content = mock_stderr.getvalue()
            self.assertNotIn(
                "claude.ai connectors are disabled",
                stderr_content,
                "Inner CLI warning must not leak into parent sys.stderr"
            )
            self.assertEqual(
                stderr_content,
                "",
                "Parent sys.stderr must remain clean during agentic review"
            )

            # 4. Verify debug_log captured the child stderr lines
            logged_messages = [call.args[0] for call in mock_debug_log.call_args_list if call.args]
            has_child_stderr_log = any("agentic review child stderr" in msg for msg in logged_messages)
            self.assertTrue(has_child_stderr_log, "Child stderr should be logged to debug_log")
            logged_warning = any("claude.ai connectors are disabled" in msg for msg in logged_messages)
            self.assertTrue(logged_warning, "The actual warning text should be recorded in debug_log")

            # 5. Verify the structured review findings were preserved intact
            self.assertIsNotNone(vulns)
            self.assertEqual(len(vulns), 1)
            self.assertEqual(vulns[0]["category"], "hardcoded_secret")
            self.assertEqual(vulns[0]["filePath"], "src/auth.ts")
            self.assertEqual(vulns[0]["severity"], "high")
            self.assertEqual(vulns[0]["vulnerableCode"], "const API_KEY = 'secret';")

    def test_agentic_review_clean_commit_leaves_sys_stderr_empty(self):
        """Verify that on a clean commit with no findings, child stderr warning is absorbed
        and does not trigger a false-positive asyncRewake body via sys.stderr."""
        class MockClaudeAgentOptions:
            def __init__(self, **kwargs):
                self.stderr = kwargs.get("stderr")

        class MockResultMessage:
            def __init__(self):
                self.subtype = "success"
                self.structured_output = {"findings": []}
                self.usage = {"input_tokens": 50, "output_tokens": 10}
                self.total_cost_usd = 0.0005

        warning_line = "⚠ claude.ai connectors are disabled\n"

        async def mock_query(prompt, options):
            if options.stderr and callable(options.stderr):
                options.stderr(warning_line)
            else:
                sys.stderr.write(warning_line)
            yield MockResultMessage()

        mock_sdk = MagicMock()
        mock_sdk.ClaudeAgentOptions = MockClaudeAgentOptions
        mock_sdk.ResultMessage = MockResultMessage
        mock_sdk.query = mock_query

        with patch.dict(sys.modules, {"claude_agent_sdk": mock_sdk}), \
             patch("llm.debug_log"), \
             patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:

            guidance, vulns, metrics = llm.agentic_review(
                repo_dir=".",
                diff_files=[("src/clean.ts", "+const x = 1;")],
                touched_paths=["src/clean.ts"],
            )

            # No vulns found
            self.assertEqual(vulns, [])
            # Parent sys.stderr must be completely empty (not contaminated by warning)
            self.assertEqual(mock_stderr.getvalue(), "")

    def test_single_turn_sdk_also_supplies_callable_stderr(self):
        """Verify sibling _call_claude_via_sdk maintains consistent stderr capture."""
        captured_options = []

        class MockClaudeAgentOptions:
            def __init__(self, **kwargs):
                self.stderr = kwargs.get("stderr")
                captured_options.append(self)

        class MockResultMessage:
            def __init__(self):
                self.subtype = "success"
                self.structured_output = {"findings": []}
                self.usage = {}
                self.total_cost_usd = 0.0

        async def mock_query(prompt, options):
            if options.stderr and callable(options.stderr):
                options.stderr("child stderr from 3P call\n")
            yield MockResultMessage()

        mock_sdk = MagicMock()
        mock_sdk.ClaudeAgentOptions = MockClaudeAgentOptions
        mock_sdk.ResultMessage = MockResultMessage
        mock_sdk.query = mock_query

        with patch.dict(sys.modules, {"claude_agent_sdk": mock_sdk}), \
             patch("llm.debug_log") as mock_debug_log, \
             patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:

            res = llm._call_claude_via_sdk(
                prompt="test prompt",
                output_schema={"type": "object"},
            )

            self.assertEqual(len(captured_options), 1)
            self.assertIsNotNone(captured_options[0].stderr)
            self.assertTrue(callable(captured_options[0].stderr))
            self.assertEqual(mock_stderr.getvalue(), "")

            logged = [call.args[0] for call in mock_debug_log.call_args_list if call.args]
            self.assertTrue(any("3P sdk-single-turn child stderr" in msg for msg in logged))


if __name__ == "__main__":
    unittest.main()
