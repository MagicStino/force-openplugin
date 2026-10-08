import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "build.py"
spec = importlib.util.spec_from_file_location("builder", SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class BuildTests(unittest.TestCase):
    def test_inventory_and_input_preservation(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "stock.img"
            data = b"PK\x03\x04" + bytes(range(256)) * 8192
            image.write_bytes(data)
            report = builder.inspect_image(image)
            self.assertEqual(report, builder.inspect_image(image))
            self.assertEqual(report["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(report["size_bytes"], len(data))
            self.assertEqual(report["container_hints_unverified"], ["ZIP"])
            self.assertEqual(image.read_bytes(), data)

    def test_build_fails_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "stock.img"
            output = Path(temp) / "custom.img"
            image.write_bytes(b"unverified firmware")
            result = subprocess.run([sys.executable, str(SCRIPT), "build",
                                     str(image), "--output", str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Build blocked", result.stderr)
            self.assertFalse(output.exists())

    def test_reject_empty_and_input_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "stock.img"
            image.write_bytes(b"")
            with self.assertRaises(ValueError):
                builder.inspect_image(image)
            image.write_bytes(b"stock")
            result = subprocess.run([sys.executable, str(SCRIPT), "inspect",
                                     str(image), "--output", str(image)],
                                    capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(image.read_bytes(), b"stock")

if __name__ == "__main__":
    unittest.main()
