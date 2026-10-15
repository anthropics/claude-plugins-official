import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills/skill-creator/scripts/quick_validate.py"
spec = importlib.util.spec_from_file_location("quick_validate", SCRIPT)
quick_validate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quick_validate)


class RequiredTextTests(unittest.TestCase):
    def validate(self, name, description):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "SKILL.md").write_text(
                f'---\nname: "{name}"\ndescription: "{description}"\n---\n',
                encoding="utf-8",
            )
            return quick_validate.validate_skill(directory)

    def test_rejects_empty_or_whitespace_only_required_fields(self):
        for field in ("name", "description"):
            for value in ("", "   "):
                with self.subTest(field=field, value=value):
                    fields = {"name": "example", "description": "Useful skill"}
                    fields[field] = value
                    valid, message = self.validate(**fields)
                    self.assertFalse(valid)
                    self.assertIn(field, message.lower())

    def test_accepts_nonempty_required_fields(self):
        self.assertTrue(self.validate("example", "Useful skill")[0])


if __name__ == "__main__":
    unittest.main()
