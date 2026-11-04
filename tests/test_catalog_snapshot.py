"""Ensure the shipping snapshot fits and is accepted by the native manager."""
import json, subprocess, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class CatalogSnapshotTest(unittest.TestCase):
    def test_native_snapshot(self):
        path = ROOT / 'website/catalog.json'
        count = len(json.loads(path.read_text())['plugins'])
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / 'snapshot'
            subprocess.run(['cc', '-O2', str(ROOT / 'tests/test_catalog_snapshot.c'), '-lpthread', '-ldl', '-lm', '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary), str(path), str(count)], check=True, capture_output=True, text=True)
            self.assertIn(f'{count} entries', result.stdout)
