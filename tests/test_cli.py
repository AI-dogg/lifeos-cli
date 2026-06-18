from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lifeos_cli.main import DEFAULT_BASE_URL, main


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str]:
        stdout = io.StringIO()
        code = main(list(args), stdout=stdout)
        return code, stdout.getvalue()

    def test_help_describes_growth_passport(self) -> None:
        code, output = self.run_cli("help")

        self.assertEqual(code, 0)
        self.assertIn("LifeOS Growth Passport CLI", output)
        self.assertIn("personal growth passport", output)
        self.assertIn("Command map:", output)
        self.assertIn("Dimensions:", output)
        self.assertIn("Asset kinds:", output)
        self.assertNotIn("LifeOS CLI 第一版", output)

    def test_schema_is_json_and_ok(self) -> None:
        code, output = self.run_cli("schema")

        self.assertEqual(code, 0)
        payload = json.loads(output)
        self.assertTrue(payload["ok"])
        self.assertIn("commands", payload)

    def test_validation_error_reports_missing_dimension(self) -> None:
        code, output = self.run_cli(
            "fact",
            "add",
            "--statement",
            "I learned how to test the growth passport CLI.",
            "--name",
            "Tester",
            "--password",
            "not-a-real-password",
        )

        self.assertEqual(code, 2)
        payload = json.loads(output)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "validation_error")
        self.assertIn(
            {"field": "dimension", "reason": "required"},
            payload["fieldErrors"],
        )

    def test_default_base_url_points_to_hosted_api(self) -> None:
        self.assertEqual(DEFAULT_BASE_URL, "https://106.55.134.110/lifeos")


if __name__ == "__main__":
    unittest.main()
