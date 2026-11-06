import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CatalogNavigation(unittest.TestCase):
 def test_order_letters_metadata_and_queue_identity(self):
  with tempfile.TemporaryDirectory() as tmp:
   binary=Path(tmp)/'navigation'
   subprocess.run(['cc','-std=gnu11',str(ROOT/'tests/test_catalog_navigation.c'),'-lpthread','-ldl','-lm','-o',str(binary)],check=True)
   subprocess.run([str(binary)],check=True)
