import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.run_eval import iter_stdout_chunks, run_eval, run_single_query


class IterStdoutChunksTest(unittest.TestCase):
    def test_reads_a_pipe_without_select(self):
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write('✓'.encode()); sys.stdout.flush()",
            ],
            stdout=subprocess.PIPE,
        )

        output = b"".join(iter_stdout_chunks(process, timeout=5))
        process.wait()
        process.stdout.close()

        self.assertEqual("✓", output.decode("utf-8"))

    def test_timeout_is_not_reported_as_a_negative_trigger(self):
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            stdout=subprocess.PIPE,
        )

        try:
            with self.assertRaises(subprocess.TimeoutExpired):
                b"".join(iter_stdout_chunks(process, timeout=0.01))
        finally:
            process.kill()
            process.wait()
            process.stdout.close()

    def test_registers_a_real_skill_and_removes_it(self):
        original_popen = subprocess.Popen

        with tempfile.TemporaryDirectory() as project_root:

            def fake_popen(_cmd, **_kwargs):
                skill_dirs = list(
                    (Path(project_root) / ".claude" / "skills").iterdir()
                )
                self.assertEqual(1, len(skill_dirs))
                skill_file = skill_dirs[0] / "SKILL.md"
                skill_text = skill_file.read_text(encoding="utf-8")
                self.assertIn(f"name: {skill_dirs[0].name}", skill_text)
                self.assertIn("✓ description", skill_text)

                clean_name = skill_dirs[0].name
                events = [
                    {
                        "type": "stream_event",
                        "event": {
                            "type": "content_block_start",
                            "content_block": {
                                "type": "tool_use",
                                "name": "Skill",
                            },
                        },
                    },
                    {
                        "type": "stream_event",
                        "event": {
                            "type": "content_block_delta",
                            "delta": {
                                "type": "input_json_delta",
                                "partial_json": json.dumps({"skill": clean_name}),
                            },
                        },
                    },
                ]
                stream = "\n".join(json.dumps(event) for event in events) + "\n"
                return original_popen(
                    [sys.executable, "-c", f"print({stream!r}, end='')"],
                    stdout=subprocess.PIPE,
                )

            with mock.patch("scripts.run_eval.subprocess.Popen", fake_popen):
                triggered = run_single_query(
                    query="test query",
                    skill_name="test",
                    skill_description="✓ description",
                    timeout=5,
                    project_root=project_root,
                )

            self.assertTrue(triggered)
            self.assertEqual(
                [], list((Path(project_root) / ".claude" / "skills").iterdir())
            )


class RunEvalTest(unittest.TestCase):
    def test_worker_failure_aborts_instead_of_recording_false(self):
        class FailedFuture:
            def result(self):
                raise subprocess.TimeoutExpired(["claude", "-p"], 30)

        failed_future = FailedFuture()

        class FakeExecutor:
            def __init__(self, **_kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def submit(self, *_args, **_kwargs):
                return failed_future

        eval_set = [{"query": "test query", "should_trigger": True}]
        with mock.patch("scripts.run_eval.ProcessPoolExecutor", FakeExecutor), mock.patch(
            "scripts.run_eval.as_completed", side_effect=lambda futures: futures
        ):
            with self.assertRaises(subprocess.TimeoutExpired):
                run_eval(
                    eval_set=eval_set,
                    skill_name="test",
                    description="test description",
                    num_workers=1,
                    timeout=30,
                    project_root=Path.cwd(),
                )


if __name__ == "__main__":
    unittest.main()
