import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
class RemoteAccessTest(unittest.TestCase):
    def test_device_credentials_and_disable_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            t=Path(td);d=t/'data/openplugin/ssh';shadow=t/'shadow'
            shadow.write_text('root:*:15069:0:99999:7:::\nother:!:1:2:3:4:5:6:7\n')
            original=shadow.read_text();(t/"stock-shadow").write_text(original)
            script=t/'remote.sh'
            s=(ROOT/'runtime/remote-access.sh').read_text().replace('/data/openplugin',str(t/'data/openplugin')).replace('/etc/shadow',str(shadow)).replace('/run/sshd',str(t/'run')).replace('/run/openplugin-shadow-mounted',str(t/'mounted'))
            script.write_text(s)
            bin=t/'bin';bin.mkdir()
            for name,body in [('chown','exit 0'),('mount','cp \"$2\" \"$3\"'),('umount',f'cp {t}/stock-shadow \"$1\"'),('systemctl','[ "${FAIL_START:-0}" != 1 ] || [ "$1" != start ]')]:
                p=bin/name;p.write_text('#!/bin/sh\n'+body+'\n');p.chmod(0o755)
            env=dict(os.environ,PATH=str(bin)+':'+os.environ['PATH'])
            def run(action,**extra):return subprocess.run(['sh',str(script),action],env=dict(env,**extra),capture_output=True)
            self.assertEqual(run('prepare').returncode,0)
            password=(d/'password').read_text();self.assertEqual(password,"mpc")
            self.assertEqual((d/'password').stat().st_mode & 0o777,0o600)
            self.assertEqual(shadow.read_text(),original)
            self.assertIn('other:!:1:2:3:4:5:6:7',shadow.read_text())
            self.assertEqual(run('prepare').returncode,0)
            self.assertEqual((d/'password').read_text(),password)
            self.assertEqual(run('disable').returncode,0)
            self.assertEqual(shadow.read_text(),original)
            self.assertNotEqual(run('prepare').returncode,0)
            self.assertNotEqual(run('enable',FAIL_START='1').returncode,0)
            self.assertTrue((d/'disabled').exists())
            self.assertEqual(shadow.read_text(),original)
            self.assertEqual(run('enable').returncode,0)
            self.assertFalse((d/'disabled').exists())
