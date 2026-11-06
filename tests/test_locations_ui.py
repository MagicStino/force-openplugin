import subprocess
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class LocationsUI(unittest.TestCase):
    def test_confirmation_and_readonly_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            test=Path(tmp)/'test'
            subprocess.run(['cc','-std=gnu11',str(ROOT/'tests/test_locations_ui.c'),'-lpthread','-ldl','-lm','-o',str(test)],check=True,capture_output=True)
            subprocess.run([str(test)],check=True,capture_output=True)
