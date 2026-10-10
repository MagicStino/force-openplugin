"""Offline codec/cache regression."""
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PreviewTest(unittest.TestCase):
 def test_offline_cache(self):
  with tempfile.TemporaryDirectory() as tmp:
   binary=Path(tmp)/"test"
   subprocess.run(["cc","-std=gnu11","-O2",str(ROOT/"tests/test_previews.c"),"-lpthread","-ldl","-lm","-o",str(binary)],check=True,capture_output=True)
   subprocess.run([str(binary)],check=True,capture_output=True)
