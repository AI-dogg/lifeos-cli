from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lifeos_cli.main import DEFAULT_BASE_URL, main


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str]:
        stdout = io.StringIO()
        original_stdin = sys.stdin
        original_env = {
            key: os.environ.get(key)
            for key in (
                "LIFEOS_CLI_CONFIG",
                "LIFEOS_USER_ID",
                "LIFEOS_USER_TOKEN",
                "LIFEOS_USER_NAME",
                "LIFEOS_NAME",
                "LIFEOS_PASSWORD",
            )
        }
        try:
            sys.stdin = io.StringIO("")
            with tempfile.TemporaryDirectory() as tmpdir:
                os.environ["LIFEOS_CLI_CONFIG"] = str(Path(tmpdir) / "cli.env")
                for key in original_env:
                    if key != "LIFEOS_CLI_CONFIG":
                        os.environ.pop(key, None)
                code = main(list(args), stdout=stdout)
        finally:
            sys.stdin = original_stdin
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        return code, stdout.getvalue()

    def test_help_prefers_record_command(self) -> None:
        code, output = self.run_cli("help")

        self.assertEqual(code, 0)
        self.assertIn("LifeOS CLI", output)
        self.assertIn("lifeos record --text", output)
        self.assertIn("默认记录入口", output)
        self.assertIn("常用记录：", output)
        self.assertIn("怎么选择：", output)
        self.assertNotIn("LifeOS CLI 第一版", output)
        self.assertNotIn("https://106.55.134.110", output)
        self.assertNotIn("LIFEOS_CLI_BASE_URL", output)
        self.assertNotIn("fieldErrors", output)
        self.assertNotIn("schema", output.lower())
        self.assertNotIn("token", output.lower())

    def test_schema_is_json_and_ok(self) -> None:
        code, output = self.run_cli("schema")

        self.assertEqual(code, 0)
        payload = json.loads(output)
        self.assertTrue(payload["ok"])
        self.assertIn("commands", payload)
        self.assertTrue(payload["capabilities"]["recordCommand"])
        self.assertTrue(payload["capabilities"]["rawCapture"])
        self.assertTrue(payload["capabilities"]["ruleProjection"])
        self.assertIn("record", payload["commands"])

    def test_record_missing_text_validates_before_network(self) -> None:
        code, output = self.run_cli(
            "record",
            "--name",
            "Tester",
            "--password",
            "not-a-real-password",
        )

        self.assertEqual(code, 2)
        payload = json.loads(output)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["command"], "record")
        self.assertEqual(payload["code"], "validation_error")
        self.assertIn({"field": "text", "reason": "required"}, payload["fieldErrors"])

    def test_record_missing_identity_is_config_error(self) -> None:
        code, output = self.run_cli("record", "--text", "今天完成 LifeOS 架构设计")

        self.assertEqual(code, 5)
        payload = json.loads(output)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["command"], "record")
        self.assertEqual(payload["code"], "config_error")

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
