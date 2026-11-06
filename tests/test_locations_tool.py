"""Real migration helper against isolated files, never live Force settings."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class LocationsTool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory()
        cls.tool = Path(cls.build.name)/'locations-tool'
        subprocess.run(['c++','-std=c++17','-DOPENPLUGIN_TEST','-Wall','-Wextra','-Werror',
                        str(ROOT/'native/locations_tool.cpp'),str(ROOT/'native/third_party/tinyxml2/tinyxml2.cpp'),
                        '-o',str(cls.tool)],check=True,capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.dir=Path(self.temp.name)
        self.source=self.dir/'internal'/'Synths';self.source.mkdir(parents=True)
        self.target=self.dir/'SSD'/'Synths';self.target.mkdir(parents=True)
        self.settings=self.dir/'MPC.settings';self.state=self.dir/'.pluginmgr-installed'
        self.plan=self.dir/'plan.xml';self.records=[]
        self.doc=ET.Element('PROPERTIES')
        ET.SubElement(self.doc,'VALUE',name='Content.Manager.Directory',val=str(self.target.parent))
        value=ET.SubElement(self.doc,'VALUE',name='pluginList-arm')
        self.plugins=ET.SubElement(value,'KNOWNPLUGINS')
        self.bin=self.dir/'bin';self.bin.mkdir()
        pidof=self.bin/'pidof';pidof.write_text('#!/bin/sh\nexit 1\n');pidof.chmod(0o755)
        self.env=dict(os.environ,PATH=str(self.bin)+':'+os.environ['PATH'])

    def plugin(self,id='test',record=True,kind='instrument',name=None):
        name=name or 'Test - VST - '+id
        folder=self.source/name;folder.mkdir()
        (folder/'plugin.so').write_bytes(b'ELF fixture data')
        (folder/'Plugin Skins').mkdir();(folder/'Plugin Skins'/'TUI.json').write_text('{}')
        manifest=dict(id=id,version='1.0',kind=kind,layout='portable',uid=id,so='plugin.so',skin=name)
        (folder/'mpc-plugin.json').write_text(json.dumps(manifest))
        ET.SubElement(self.plugins,'PLUGIN',name=name,format='VST',uid=id,file=str(folder/'plugin.so'))
        if record:self.records.append(id+' 1.0\n')
        return folder

    def save(self):
        self.settings.write_bytes(ET.tostring(self.doc));self.state.write_text(''.join(self.records))

    def run_tool(self,mode,check=True):
        args=[str(self.tool),mode,str(self.settings),str(self.state)]
        if mode in ('eligible','plan','move'):args += [str(self.target),str(self.plan)]
        run=subprocess.run(args,env=self.env,capture_output=True,text=True)
        if check:self.assertEqual(run.returncode,0,run.stderr)
        return run

    def test_move_only_manager_owned_vsts_and_preserve_originals(self):
        managed=self.plugin();unmanaged=self.plugin('manual',False)
        addin=self.plugin('addon',True,'addin')
        manager=self.plugin('openplugin-manager',True)
        official=self.plugin('official',False,name='AIR Music Technology - MPC - Example')
        presets=managed/'Presets';presets.mkdir()
        ET.ElementTree(ET.Element('Preset',file=str(managed/'plugin.so'))).write(presets/'test.xpl')
        (managed/'user-data').write_text('user patch')
        self.save();before=self.settings.read_bytes()
        self.run_tool('plan');self.assertEqual(self.settings.read_bytes(),before)
        self.run_tool('move')
        settings=ET.parse(self.settings)
        entry=settings.find('.//PLUGIN[@uid="test"]')
        copied=self.target/managed.name
        self.assertEqual(entry.get('file'),str(copied/'plugin.so'))
        self.assertEqual((copied/'plugin.so').read_bytes(),(managed/'plugin.so').read_bytes())
        self.assertEqual((copied/'user-data').read_text(),'user patch')
        self.assertEqual(ET.parse(copied/'Presets/test.xpl').getroot().get('file'),str(copied/'plugin.so'))
        self.assertTrue(managed.exists())
        for folder in (unmanaged,addin,manager,official):
            self.assertFalse((self.target/folder.name).exists())
            self.assertTrue(folder.exists())
        self.assertEqual(settings.find('.//Location').text,str(self.target))
        recovery=list(self.dir.glob('MPC.settings.move-recovery-*'))
        self.assertEqual(len(recovery),1)
        self.assertEqual((recovery[0]/'MPC.settings.before').read_bytes(),before)
        self.assertTrue((recovery[0]/'COMMITTED').exists())
        self.assertEqual(self.run_tool('plan',False).returncode,1) # already there, no duplicate move

    def test_drive_to_drive_updates_internal_compatibility_link(self):
        folder=self.plugin();self.save();self.run_tool('plan');self.run_tool('move')
        self.assertTrue(folder.is_symlink())
        self.target=self.dir/'USB'/'Synths';self.target.mkdir(parents=True)
        self.run_tool('plan');self.run_tool('move')
        self.assertEqual(folder.readlink(),self.target/folder.name)
        doc=ET.parse(self.settings)
        self.assertEqual(doc.find('.//VALUE[@name="OpenPlugin.InstallTarget"]').get('val'),str(self.target))

    def test_interrupted_copyback_can_retry_verified_existing_copy(self):
        folder=self.plugin();self.save();self.run_tool('plan');self.run_tool('move')
        self.target=self.source;self.run_tool('plan')
        self.env['OPENPLUGIN_FAIL_AFTER_COPY']='1'
        self.assertNotEqual(self.run_tool('move',False).returncode,0)
        self.assertFalse(folder.is_symlink())
        del self.env['OPENPLUGIN_FAIL_AFTER_COPY']
        self.run_tool('plan');self.run_tool('move')
        self.assertEqual(ET.parse(self.settings).find('.//PLUGIN').get('file'),str(folder/'plugin.so'))

    def test_discovery_defers_content_reads_until_review(self):
        folder=self.plugin();self.save()
        (folder/'runtime-path.txt').write_text(str(folder))
        self.run_tool('eligible')
        self.assertFalse(self.plan.exists())
        self.assertNotEqual(self.run_tool('plan',False).returncode,0)

    def test_conflict_blocks_everything_before_copy(self):
        folder=self.plugin();self.save();before=self.settings.read_bytes()
        (self.target/folder.name).mkdir()
        self.assertNotEqual(self.run_tool('plan',False).returncode,0)
        self.assertEqual(self.settings.read_bytes(),before)
        self.assertTrue((folder/'plugin.so').exists())

    def test_revalidates_ownership_after_confirmation(self):
        folder=self.plugin();self.save();self.run_tool('plan')
        before=self.settings.read_bytes();self.state.write_text('')
        self.assertNotEqual(self.run_tool('move',False).returncode,0)
        self.assertEqual(self.settings.read_bytes(),before)
        self.assertFalse((self.target/folder.name).exists())

    def test_running_app_blocks_mutation(self):
        folder=self.plugin();self.save();self.run_tool('plan')
        (self.bin/'pidof').write_text('#!/bin/sh\nexit 0\n')
        self.assertNotEqual(self.run_tool('move',False).returncode,0)
        self.assertFalse((self.target/folder.name).exists())

    def test_unsupported_absolute_reference_blocks_move(self):
        folder=self.plugin();(folder/'config.txt').write_text(str(folder/'data'))
        self.save();before=self.settings.read_bytes()
        run=self.run_tool('plan',False)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('absolute references',run.stderr)
        self.assertEqual(self.settings.read_bytes(),before)

    def test_external_symlink_blocks_move(self):
        folder=self.plugin();(folder/'external').symlink_to('/etc')
        self.save();self.assertNotEqual(self.run_tool('plan',False).returncode,0)

    def test_relative_internal_symlink_is_preserved(self):
        folder=self.plugin();(folder/'alias').symlink_to('plugin.so')
        self.save();self.run_tool('plan');self.run_tool('move')
        self.assertEqual(os.readlink(self.target/folder.name/'alias'),'plugin.so')

    def test_manual_repair_only_owned_roots_with_skin_files(self):
        self.plugin();self.plugin('manual',False);self.save()
        self.run_tool('repair')
        self.assertEqual([n.text for n in ET.parse(self.settings).findall('.//Location')],[str(self.source)])
        after=self.settings.read_bytes();self.run_tool('repair');self.assertEqual(self.settings.read_bytes(),after)
        self.assertEqual(len(list(self.dir.glob('*.bak-repair-*'))),1)

    def test_missing_skin_files_are_not_claimed_repaired(self):
        folder=self.plugin();(folder/'Plugin Skins/TUI.json').unlink();self.save()
        before=self.settings.read_bytes();result=self.run_tool('repair')
        self.assertIn('1 plugins have no skin files',result.stdout)
        self.assertEqual(self.settings.read_bytes(),before)

    def test_interrupted_copy_never_switches_settings_or_removes_originals(self):
        folder=self.plugin();self.save();self.run_tool('plan')
        before=self.settings.read_bytes();self.env['OPENPLUGIN_FAIL_AFTER_COPY']='1'
        self.assertNotEqual(self.run_tool('move',False).returncode,0)
        self.assertEqual(self.settings.read_bytes(),before)
        self.assertTrue((folder/'plugin.so').exists())
        self.assertEqual((self.target/folder.name/'plugin.so').read_bytes(),(folder/'plugin.so').read_bytes())

    def test_repair_check_is_readonly_and_detects_noop(self):
        self.plugin();self.save();before=self.settings.read_bytes()
        self.run_tool('check-repair')
        self.assertEqual(self.settings.read_bytes(),before)
        self.run_tool('repair')
        result=self.run_tool('check-repair',False)
        self.assertEqual(result.returncode,2)
        self.assertIn('No missing skin search locations',result.stdout)

    def test_missing_drive_and_changed_plan_are_rejected(self):
        folder=self.plugin();self.save();self.run_tool('plan')
        plan=ET.parse(self.plan);plan.getroot().set('device','99999');plan.write(self.plan)
        self.assertNotEqual(self.run_tool('move',False).returncode,0)
        self.assertFalse((self.target/folder.name).exists())
        self.target.rmdir();self.target.parent.rmdir()
        self.assertNotEqual(self.run_tool('plan',False).returncode,0)



    def test_repeated_repair_preserves_later_install_and_preferences(self):
        self.plugin();self.save();self.run_tool('repair')
        self.doc=ET.parse(self.settings).getroot()
        locations=self.doc.find('./VALUE[@name="SynthContentLocations"]/SynthContentLocations')
        ET.SubElement(locations,'Location').text='/media/Later drive/Synths'
        ET.SubElement(self.doc,'VALUE',name='UnrelatedPreference',val='keep this')
        self.save();before=self.settings.read_bytes()
        self.run_tool('repair')
        self.assertEqual(self.settings.read_bytes(),before)
        self.assertEqual(len(list(self.dir.glob('*.bak-repair-*'))),1)

    def test_progress_is_separate_from_critical_log(self):
        folder=self.plugin();(folder/'rom.bin').write_bytes(b'x'*(200000))
        self.save();self.run_tool('plan');self.run_tool('move')
        progress=json.loads((self.dir/'.pluginmgr-locations-progress.json').read_text())
        self.assertEqual(progress['state'],'done')
        self.assertEqual(progress['bytes_done'],progress['bytes_total'])
        self.assertEqual(progress['plugin_index'],1)
        log=(self.dir/'.pluginmgr-locations-debug.log').read_text()
        self.assertNotIn('rom.bin',log)
        self.assertEqual(len(log.splitlines()),5)
        self.assertIn('COMMIT',log)

    def test_preparation_can_use_isolated_progress_snapshot(self):
        self.plugin();self.save()
        shared=self.dir/'.pluginmgr-locations-progress.json';shared.write_text('other operation')
        isolated=self.dir/'preview-progress.json';self.env['OPENPLUGIN_PROGRESS_FILE']=str(isolated)
        self.run_tool('plan')
        self.assertEqual(shared.read_text(),'other operation')
        self.assertEqual(json.loads(isolated.read_text())['state'],'done')

    def test_preparation_reports_work_without_per_file_logging(self):
        folder=self.plugin();(folder/'bank.rom').write_bytes(b'x'*200000)
        self.save();before=self.settings.read_bytes();self.run_tool('plan')
        progress=json.loads((self.dir/'.pluginmgr-locations-progress.json').read_text())
        self.assertGreaterEqual(progress['bytes_checked'],200000)
        self.assertGreaterEqual(progress['files_checked'],4)
        self.assertEqual(progress['plugin_count'],1)
        self.assertEqual(progress['plugin_index'],1)
        self.assertEqual(self.settings.read_bytes(),before)
        self.assertNotIn('bank.rom',(self.dir/'.pluginmgr-locations-debug.log').read_text())

    def test_failure_report_keeps_phase_plugin_and_originals(self):
        folder=self.plugin();self.save();self.run_tool('plan')
        self.env['OPENPLUGIN_FAIL_AFTER_COPY']='1'
        before=self.settings.read_bytes();self.assertNotEqual(self.run_tool('move',False).returncode,0)
        progress=json.loads((self.dir/'.pluginmgr-locations-progress.json').read_text())
        self.assertEqual(progress['state'],'failed')
        self.assertEqual(progress['plugin'],folder.name)
        self.assertTrue(progress['original_files_retained'])
        self.assertEqual(self.settings.read_bytes(),before)
        log=(self.dir/'.pluginmgr-locations-debug.log').read_text()
        self.assertIn('ERROR',log);self.assertNotIn('COMMIT',log)

    def test_critical_log_stays_bounded(self):
        self.plugin();self.save()
        log=self.dir/'.pluginmgr-locations-debug.log'
        log.write_text(('older event '*40+'\n')*1000)
        self.run_tool('repair')
        self.assertLessEqual(log.stat().st_size,8192)
        self.assertIn('DONE',log.read_text().splitlines()[-1])

    def test_background_scan_does_not_create_logs(self):
        self.plugin();self.save();self.run_tool('inspect');self.run_tool('eligible');self.run_tool('check-repair')
        self.assertFalse((self.dir/'.pluginmgr-locations-debug.log').exists())
        self.assertTrue((self.dir/'.pluginmgr-locations-progress.json').is_file())

    def test_repair_and_move_preserve_embedded_xml_attribute_whitespace(self):
        self.plugin()
        embedded='<Default>\n  <MIDI value="x\ty"/>\r\n</Default>'
        ET.SubElement(self.doc,'VALUE',name='Unrelated.EmbeddedXML',val=embedded)
        self.save();self.run_tool('repair')
        self.assertEqual(ET.parse(self.settings).find('./VALUE[@name="Unrelated.EmbeddedXML"]').get('val'),embedded)
        self.run_tool('plan');self.run_tool('move')
        self.assertEqual(ET.parse(self.settings).find('./VALUE[@name="Unrelated.EmbeddedXML"]').get('val'),embedded)

    def return_tool(self,mode,check=True):
        args=[str(self.tool),mode,str(self.settings),str(self.state)]
        if mode!='check-return':args.append(str(self.dir/'return.xml'))
        run=subprocess.run(args,env=self.env,capture_output=True,text=True)
        if check:self.assertEqual(run.returncode,0,run.stderr)
        return run

    def test_return_preserves_later_preferences_and_skin_roots(self):
        folder=self.plugin();ET.ElementTree(ET.Element('Preset',file=str(folder/'plugin.so'))).write(folder/'test.xpl')
        self.save();self.assertEqual(self.return_tool('check-return',False).returncode,2)
        self.run_tool('plan');self.run_tool('move');self.return_tool('check-return');self.return_tool('plan-return')
        doc=ET.parse(self.settings);ET.SubElement(doc.getroot(),'VALUE',name='NewPreference',val='keep')
        ET.SubElement(doc.find('.//SynthContentLocations'),'Location').text='/media/Later/Synths'
        entries=doc.find('.//KNOWNPLUGINS');ET.SubElement(entries,'PLUGIN',uid='later',file='/some/later/plugin.so',format='VST')
        doc.write(self.settings);self.return_tool('return')
        doc=ET.parse(self.settings)
        self.assertEqual(doc.find('.//PLUGIN[@uid="test"]').get('file'),str(folder/'plugin.so'))
        self.assertEqual(doc.find('.//VALUE[@name="NewPreference"]').get('val'),'keep')
        self.assertIsNotNone(doc.find('.//PLUGIN[@uid="later"]'))
        self.assertIn('/media/Later/Synths',[e.text for e in doc.findall('.//Location')])
        self.assertTrue((self.target/folder.name/'plugin.so').exists())
        self.assertEqual(self.return_tool('check-return',False).returncode,2)
        before=self.settings.read_bytes();self.return_tool('return');self.assertEqual(self.settings.read_bytes(),before)

    def test_return_copies_latest_content_and_blocks_running_app(self):
        folder=self.plugin();self.save();self.run_tool('plan');self.run_tool('move');self.return_tool('plan-return')
        self.assertTrue(folder.is_symlink())
        before=self.settings.read_bytes();copied=self.target/folder.name
        (copied/'new-preset').write_text('must keep')
        (copied/'plugin.so').write_bytes(b'updated binary')
        (self.bin/'pidof').write_text('#!/bin/sh\nexit 0\n')
        self.assertNotEqual(self.return_tool('return',False).returncode,0)
        self.assertEqual(self.settings.read_bytes(),before)
        (self.bin/'pidof').write_text('#!/bin/sh\nexit 1\n')
        self.return_tool('return')
        self.assertFalse(folder.is_symlink())
        self.assertEqual((folder/'new-preset').read_text(),'must keep')
        self.assertEqual((folder/'plugin.so').read_bytes(),b'updated binary')

    def test_return_refuses_missing_original_and_changed_registration(self):
        folder=self.plugin();self.save();self.run_tool('plan');self.run_tool('move');self.return_tool('plan-return')
        before=self.settings.read_bytes();original=folder/'plugin.so';data=original.read_bytes();original.unlink()
        self.assertNotEqual(self.return_tool('return',False).returncode,0)
        self.assertEqual(self.settings.read_bytes(),before)
        original.write_bytes(data)
        doc=ET.parse(self.settings);doc.find('.//PLUGIN').set('file','/other/plugin.so');doc.write(self.settings)
        before=self.settings.read_bytes();self.assertNotEqual(self.return_tool('return',False).returncode,0)
        self.assertEqual(self.settings.read_bytes(),before)

    def test_incompatible_plugin_stays_without_blocking_other_plugins(self):
        movable=self.plugin('movable');blocked=self.plugin('blocked')
        (blocked/'config.txt').write_text(str(blocked/'fixed-content'))
        self.save();result=self.run_tool('plan');self.assertIn('1 stay in place',result.stdout)
        self.run_tool('move');doc=ET.parse(self.settings)
        self.assertEqual(doc.find('.//PLUGIN[@uid="movable"]').get('file'),str(self.target/movable.name/'plugin.so'))
        self.assertEqual(doc.find('.//PLUGIN[@uid="blocked"]').get('file'),str(blocked/'plugin.so'))
        self.assertFalse((self.target/blocked.name).exists())

    def test_install_target_checks_unpacked_package_links(self):
        self.plugin();self.save();package=self.dir/'package';package.mkdir();(package/'payload').write_text('plugin')
        args=[str(self.tool),'install-target',str(self.settings),str(self.state),str(self.target),str(package)]
        before=self.settings.read_bytes()
        result=subprocess.run(args,env=self.env,capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),str(self.target))
        (package/'alias').symlink_to('payload')
        self.env['OPENPLUGIN_TEST_INTERNAL']=str(self.source)
        result=subprocess.run(args,env=self.env,capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),str(self.source))
        self.assertEqual(self.settings.read_bytes(),before)

    def test_install_target_detects_restored_links_in_modes_manifest(self):
        self.plugin();self.save();package=self.dir/'package';package.mkdir()
        (package/'MODES').write_text('l\tbin/python\tpython3\nx\tplugin.so\n')
        self.env['OPENPLUGIN_TEST_INTERNAL']=str(self.source)
        result=subprocess.run([str(self.tool),'install-target',str(self.settings),str(self.state),str(self.target),str(package)],env=self.env,capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),str(self.source))
