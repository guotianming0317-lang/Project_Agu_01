"""Tests for the minimal application bootstrap path."""

from __future__ import annotations

import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from app.main import main


class MainTests(unittest.TestCase):
    """Verify the demo bootstrap stays runnable."""

    def test_main_creates_database_and_prints_demo_output(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main()

            output = stdout.getvalue()
            self.assertTrue(database_path.exists())
            self.assertIn("AI Semiconductor Monitor Demo", output)
            self.assertIn("【今日主线判断】", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
