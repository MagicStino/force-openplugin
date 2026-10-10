"""Filtered catalog polling regression; no network or device changes."""
import subprocess
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class SearchPollingTest(unittest.TestCase):
    def test_idle_search_does_not_rescan(self):
        with tempfile.TemporaryDirectory(prefix="openplugin-search-") as tmp:
            binary = Path(tmp) / "test"
            subprocess.run(["cc", "-std=gnu11", "-O2", str(ROOT / "tests/test_search_poll.c"),
                            "-lpthread", "-ldl", "-lm", "-o", str(binary)],
                           check=True, capture_output=True)
            subprocess.run([str(binary)], check=True, capture_output=True)
