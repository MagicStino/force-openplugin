"""Exercise build target routing without fetching dependencies or building firmware."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'build.sh'


class EntrypointTests(unittest.TestCase):
    def run_build(self, target, key=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copyfile(SCRIPT, root / 'build.sh')
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            runner = '''#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
with open(os.environ['BUILD_TEST_LOG'], 'a') as log:
    log.write(json.dumps(args) + '\\n')
if args[:2] == ['-m', 'venv']:
    path = pathlib.Path(args[2]) / 'bin'
    path.mkdir(parents=True)
    (path / 'python').symlink_to(pathlib.Path(__file__).resolve())
'''.replace('#!/usr/bin/env python3', '#!' + shutil.which('python3'))
            (bin_dir / 'python3').write_text(runner)
            (bin_dir / 'python3').chmod(0o755)
            for tool in ('git', 'debugfs', 'e2fsck', 'readelf'):
                (bin_dir / tool).write_text('#!/bin/sh\nexit 0\n')
                (bin_dir / tool).chmod(0o755)
            (bin_dir / 'gcc').write_text('#!/bin/sh\nwhile [ "$1" != "-o" ]; do shift; done\nshift\nprintf "#!/bin/sh\\nexit 0\\n" > "$1"\nchmod +x "$1"\n')
            (bin_dir / 'gcc').chmod(0o755)
            force, mpc = root / 'Force stock.img', root / 'MPC stock.img'
            force.touch()
            mpc.touch()
            args = [str(force), str(mpc), str(root / 'output')]
            if target != 'both':
                args = ['--device', target, str(force if target == 'force' else mpc), str(root / 'output')]
            if key:
                public_key = root / 'owner key.pub'
                public_key.touch()
                args.append(str(public_key))
            log = root / 'calls.jsonl'
            env = dict(os.environ, PATH=str(bin_dir) + ':' + os.environ['PATH'], BUILD_TEST_LOG=str(log))
            result = subprocess.run(['bash', str(root / 'build.sh'), *args], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            builds = [call for call in calls if call[0].endswith('/tools/build.py')]
            expected = ['force', 'mpc-gen1'] if target == 'both' else [target]
            self.assertEqual([call[call.index('--device') + 1] for call in builds], expected)
            for call, device in zip(builds, expected):
                self.assertEqual(call[2], str(force if device == 'force' else mpc))
            native = next(call for call in calls if call[0].endswith('/tools/build_native.py'))
            self.assertEqual(native[1:], ['--ssh-key', str(public_key)] if key else [])
            self.assertTrue(any(call[:3] == ['-m', 'unittest', 'discover'] for call in calls))

    def test_target_and_optional_key_routing(self):
        for target in ('force', 'mpc-gen1', 'both'):
            for key in (False, True):
                with self.subTest(target=target, key=key):
                    self.run_build(target, key)

    def test_invalid_arguments_stop_before_setup(self):
        for args in ([], ['--device', 'unknown', 'stock.img', 'output'], ['--device', 'force']):
            result = subprocess.run(['bash', str(SCRIPT), *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Usage:', result.stderr)
