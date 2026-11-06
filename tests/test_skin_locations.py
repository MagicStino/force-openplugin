"""Exercise the actual XML helper and generated batch finalizer, without a device."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class SkinLocations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory()
        cls.helper = Path(cls.build.name) / 'skin-locations'
        subprocess.run(['c++', '-std=c++11', '-Wall', '-Wextra', '-Werror',
                        str(ROOT/'native/skin_locations.cpp'),
                        str(ROOT/'native/third_party/tinyxml2/tinyxml2.cpp'),
                        '-o', str(cls.helper)], check=True, capture_output=True)
        source = Path(cls.build.name) / 'guard.c'
        source.write_text('#include "'+str(ROOT/'native/manager.c')+'"\n'
                          'int main(int argc,char **argv) { (void)argc; '
                          'skin_write_guard(stdout,argv[1],argv[2]); return 0; }\n')
        cls.guard = Path(cls.build.name) / 'guard'
        subprocess.run(['cc', '-std=gnu11', '-O0', str(source), '-lpthread', '-ldl', '-lm',
                        '-o', str(cls.guard)], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.settings = self.dir / 'MPC.settings'
        self.roots = self.dir / 'roots'
        self.root = self.dir / 'Space & Music' / 'Synths'
        self.root.mkdir(parents=True)
        self.roots.write_text(str(self.root)+'\n')
        self.bin = self.dir / 'bin'; self.bin.mkdir()
        self.script('pidof', 'exit 1\n')
        self.log = self.dir / 'services'
        self.script('systemctl', 'echo "$*" >> "$SERVICE_LOG"\n')
        self.env = dict(os.environ, PATH=str(self.bin)+':'+os.environ['PATH'], SERVICE_LOG=str(self.log))

    def script(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/sh\n'+body); path.chmod(0o755)

    def run_helper(self):
        return subprocess.run([str(self.helper), str(self.settings), str(self.roots)],
                              env=self.env, capture_output=True, text=True)

    def locations(self):
        return [x.text for x in ET.parse(self.settings).findall('.//SynthContentLocations/Location')]

    def test_register_missing_root_and_preserve_preferences(self):
        doc = ET.Element('PROPERTIES')
        ET.SubElement(doc, 'VALUE', name='Content.Manager.Directory', val='/media/SSD')
        plugins = ET.SubElement(doc, 'VALUE', name='pluginList-arm')
        ET.SubElement(plugins, 'PLUGIN', name='Test', file=str(self.root/'Test/test.so'))
        original = ET.tostring(doc)
        self.settings.write_bytes(original); self.settings.chmod(0o640)
        self.assertEqual(self.run_helper().returncode, 0)
        self.assertEqual(self.locations(), [str(self.root)])
        self.assertEqual(next(self.dir.glob('*.bak-skins-*')).read_bytes(), original)
        self.assertEqual(self.settings.stat().st_mode & 0o777, 0o640)
        result = ET.parse(self.settings)
        self.assertEqual(result.find('./VALUE').get('val'), '/media/SSD')
        self.assertEqual(result.find('.//PLUGIN').get('file'), str(self.root/'Test/test.so'))
        saved = self.settings.read_bytes()
        self.assertEqual(self.run_helper().returncode, 0)
        self.assertEqual(self.settings.read_bytes(), saved)
        self.assertEqual(len(list(self.dir.glob('*.bak-skins-*'))), 1)

    def test_duplicates_aliases_and_trailing_slash(self):
        alias = self.dir/'alias'; alias.symlink_to(self.root, target_is_directory=True)
        self.settings.write_text('<PROPERTIES><VALUE name="SynthContentLocations">'
                                 '<SynthContentLocations><Location>'+str(alias)+'/'
                                 '</Location><Location>/offline/Synths</Location>'
                                 '</SynthContentLocations></VALUE></PROPERTIES>')
        original = self.settings.read_bytes()
        self.roots.write_text(str(self.root)+'\n'+str(self.root)+'\n')
        self.assertEqual(self.run_helper().returncode, 0)
        self.assertEqual(self.settings.read_bytes(), original)
        self.assertFalse(list(self.dir.glob('*.bak-skins-*')))

    def test_invalid_and_duplicate_settings_fail_unchanged(self):
        for data in ['<PROPERTIES>', '<OTHER/>',
                     '<PROPERTIES><VALUE name="SynthContentLocations"/>'
                     '<VALUE name="SynthContentLocations"/></PROPERTIES>']:
            self.settings.write_text(data)
            self.assertNotEqual(self.run_helper().returncode, 0)
            self.assertEqual(self.settings.read_text(), data)
        self.assertFalse(list(self.dir.glob('*.bak-skins-*')))

    def test_running_app_is_rejected(self):
        self.settings.write_text('<PROPERTIES/>')
        self.script('pidof', 'exit 0\n')
        self.assertNotEqual(self.run_helper().returncode, 0)
        self.assertEqual(self.settings.read_text(), '<PROPERTIES/>')

    def test_missing_root_is_rejected(self):
        self.settings.write_text('<PROPERTIES/>')
        self.roots.write_text('/nonexistent-openplugin-test/Synths\n')
        self.assertNotEqual(self.run_helper().returncode, 0)
        self.assertEqual(self.settings.read_text(), '<PROPERTIES/>')

    def test_batch_finalizer_handles_partial_failure(self):
        for failure in [False, True]:
            self.settings.write_text('<PROPERTIES/>')
            self.log.unlink(missing_ok=True)
            guard = subprocess.check_output([str(self.guard), str(self.helper), str(self.settings)], text=True)
            # Redirect only the generated scratch path into this test's directory.
            guard = guard.replace('SKIN_ROOTS=\'/tmp/pluginmgr/installed-skin-roots\'',
                                  'SKIN_ROOTS=\''+str(self.roots)+'\'')
            # WORK may change in future: use the assignment's own path rather than touching it.
            import re
            guard = re.sub(r"SKIN_ROOTS='[^']*'", "SKIN_ROOTS='"+str(self.roots)+"'", guard)
            body = 'set -e\n'+guard+'printf "%s\\n" "'+str(self.root)+'" >> "$SKIN_ROOTS"\n'
            body += 'exit 7\n' if failure else 'finish\necho done\n'
            run = subprocess.run(['sh', '-c', body], env=self.env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 7 if failure else 0, run.stderr)
            self.assertEqual(self.locations(), [str(self.root)])
            self.assertEqual(self.log.read_text(), 'start acvs\n')

    def test_helper_failure_still_restarts_and_reports_failure(self):
        self.settings.write_text('<PROPERTIES>')
        guard = subprocess.check_output([str(self.guard), str(self.helper), str(self.settings)], text=True)
        import re
        guard = re.sub(r"SKIN_ROOTS='[^']*'", "SKIN_ROOTS='"+str(self.roots)+"'", guard)
        run = subprocess.run(['sh', '-c', 'set -e\n'+guard+'printf "%s\\n" "'+str(self.root)+'" >> "$SKIN_ROOTS"\nfinish\necho done\n'],
                             env=self.env, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertNotIn('done', run.stdout)
        self.assertEqual(self.log.read_text(), 'start acvs\n')
        self.assertEqual(self.settings.read_text(), '<PROPERTIES>')

    def test_preserve_embedded_attribute_newlines_and_tabs(self):
        doc=ET.Element('PROPERTIES');value='<MIDI>\n  <Route value="x\ty"/>\r\n</MIDI>'
        ET.SubElement(doc,'VALUE',name='EmbeddedXML',val=value)
        self.settings.write_bytes(ET.tostring(doc))
        self.assertEqual(self.run_helper().returncode,0)
        self.assertEqual(ET.parse(self.settings).find('./VALUE[@name="EmbeddedXML"]').get('val'),value)

if __name__ == '__main__':
    unittest.main()
