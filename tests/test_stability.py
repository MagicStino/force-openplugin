"""Host-only integration: never touches device services or ROM downloads."""
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class StabilityTest(unittest.TestCase):
 def test_apply_preserves_user_nvram(self):
  with tempfile.TemporaryDirectory(prefix='openplugin-integration-') as d:
   root=Path(d);work=root/'work';stage=work/'jv-content/roms';stage.mkdir(parents=True)
   target=root/'Synths';dest=target/'sd88me - VST - JV-880/jv880-roms/roms';dest.mkdir(parents=True)
   names={'jv880_rom1.bin':32768,'jv880_rom2.bin':262144,'jv880_waverom1.bin':2097152,'jv880_waverom2.bin':2097152,'jv880_nvram.bin':32768}
   for n,size in names.items():(stage/n).write_bytes(b'R'*size)
   (dest/'jv880_nvram.bin').write_bytes(b'U'*32768)
   binary=root/'test';subprocess.run(['cc','-w','-std=gnu11','-DWORK="'+str(work)+'"',str(ROOT/'tests/test_stability.c'),'-lpthread','-ldl','-lm','-o',str(binary)],check=True,capture_output=True)
   script=root/'apply.sh';subprocess.run([str(binary),str(script),str(target)],check=True,capture_output=True)
   subprocess.run(['sh','-n',str(script)],check=True,capture_output=True);subprocess.run(['sh',str(script)],check=True,capture_output=True)
   self.assertEqual((dest/'jv880_nvram.bin').read_bytes(),b'U'*32768)
   self.assertTrue(all((dest/n).stat().st_size==size for n,size in names.items()))
   self.assertFalse((work/'jv-content').exists())
