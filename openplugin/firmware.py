"""Deterministic, unmounted rootfs injection. No signature or boot-policy patching."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from .az01 import extract, pack, parse

VERSION = '3.9.1.3-openplugin'
EPOCH = 1791417600  # 2026-10-08 00:00 UTC, metadata only
ROOT = Path(__file__).resolve().parents[1]


def quote(value):
    value = str(value)
    if any(c in value for c in ['"', '\\', '\n', '\r']):
        raise ValueError('Unsupported debugfs path characters')
    return '"' + value + '"'


def build(image, device, payload, output):
    image, payload, output = Path(image).resolve(), Path(payload).resolve(), Path(output).resolve()
    if output == image or image in output.parents:
        raise ValueError('Output must not overwrite input')
    locks = json.loads((ROOT / 'inputs.json').read_text())
    source = image.read_bytes()
    source_hash = hashlib.sha256(source).hexdigest()
    if device not in locks or source_hash != locks[device]['sha256']:
        raise ValueError('Input does not match the pinned stock image for this device')
    info, rootfs = extract(source)
    info.pop('compressed')
    del source
    if not (payload / 'usr/share/openplugin/VERSION').is_file():
        raise ValueError('Native payload missing: run tools/build_native.py first')
    native = payload / 'usr/share/Akai/Content/Synths/poloq - VST - Plugin Manager/plugin_manager.so'
    header = native.read_bytes()[:20]
    if header[:5] != b'\x7fELF\x01' or header[18:20] != b'\x28\0':
        raise ValueError('Native manager must be a 32-bit ARM ELF')
    if output.exists():
        raise ValueError('Output already exists; choose a new path')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='openplugin-', dir=output.parent) as temp:
        temp = Path(temp)
        fs = temp / 'rootfs.ext4'
        fs.write_bytes(rootfs)
        del rootfs
        shadow_override = None
        if (payload / 'usr/share/openplugin/authorized_keys').is_file():
            shadow_override = temp / 'shadow'
            subprocess.run(['debugfs', '-R', f'dump /etc/shadow {quote(shadow_override)}', str(fs)], capture_output=True, check=True)
            lines = shadow_override.read_text().splitlines()
            roots = [i for i, line in enumerate(lines) if line.startswith('root:')]
            if len(roots) != 1:
                raise ValueError('Expected exactly one root account')
            fields = lines[roots[0]].split(':')
            # Linux OpenSSH treats ! as an account lock, blocking keys as well.
            # * is an unusable password; password/interactive auth stay disabled.
            fields[1] = '*'
            lines[roots[0]] = ':'.join(fields)
            shadow_override.write_text('\n'.join(lines) + '\n')
        files = sorted(payload.rglob('*'))
        commands = [f'set_current_time @{EPOCH}']
        # Existing directories are harmless mkdir errors. File writes must all be verified below.
        manifest = {}
        for path in sorted(files, key=lambda p: (len(p.parts), str(p))):
            target = '/' + path.relative_to(payload).as_posix()
            if path.is_symlink():
                link = os.readlink(path)
                commands.append(f'symlink {quote(target)} {quote(link)}')
                manifest[target] = {'symlink': link}
            elif path.is_dir():
                commands.append(f'mkdir {quote(target)}')
            else:
                commands.append(f'write {quote(path)} {quote(target)}')
                mode = '0100755' if path.suffix == '.sh' or path.suffix == '.so' else '0100644'
                commands.append(f'set_inode_field {quote(target)} mode {mode}')
                manifest[target] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            commands += [f'set_inode_field {quote(target)} uid 0', f'set_inode_field {quote(target)} gid 0']
        if shadow_override:
            commands += ['rm /etc/shadow', f'write {quote(shadow_override)} /etc/shadow',
                         'set_inode_field /etc/shadow mode 0100600',
                         'set_inode_field /etc/shadow uid 0', 'set_inode_field /etc/shadow gid 0']
            manifest['/etc/shadow'] = {'sha256': hashlib.sha256(shadow_override.read_bytes()).hexdigest()}
        commands += [f'set_super_value wtime @{EPOCH}']
        script = temp / 'inject.txt'
        script.write_text('\n'.join(commands) + '\n')
        result = subprocess.run(['debugfs', '-w', '-f', str(script), str(fs)], capture_output=True, text=True, check=True)
        (temp / 'inject.log').write_text(result.stdout + result.stderr)
        bad = [line for line in result.stderr.splitlines() if any(t in line for t in
               ['Could not allocate', 'File not found', 'Invalid', 'Usage:', 'write: Ext2 file already exists'])]
        if bad:
            raise ValueError('rootfs injection failed: ' + '; '.join(bad))
        # Verify every injected file and link, rather than trusting debugfs's exit code.
        for target, expected in manifest.items():
            if 'sha256' in expected:
                dumped = temp / 'dump'
                subprocess.run(['debugfs', '-R', f'dump {quote(target)} {quote(dumped)}', str(fs)],
                               capture_output=True, check=True)
                if not dumped.exists() or hashlib.sha256(dumped.read_bytes()).hexdigest() != expected['sha256']:
                    raise ValueError('Injected file verification failed: ' + target)
                dumped.unlink()
            else:
                stat = subprocess.check_output(['debugfs', '-R', f'stat {quote(target)}', str(fs)], stderr=subprocess.DEVNULL, text=True)
                if expected['symlink'] not in stat:
                    raise ValueError('Injected symlink verification failed: ' + target)
        check = subprocess.run(['e2fsck', '-f', '-n', str(fs)], capture_output=True, text=True)
        if check.returncode != 0:
            raise ValueError('Read-only filesystem check failed: ' + check.stdout + check.stderr)
        modified = fs.read_bytes()
        final = pack(info, modified, VERSION)
        final_info = parse(final)
        if final_info['boards'] != info['boards'] or final_info['devices'] != info['devices']:
            raise ValueError('Device compatibility changed')
        report = dict(project_version=VERSION, device=device, input_sha256=source_hash,
                      output_sha256=hashlib.sha256(final).hexdigest(), output_size=len(final),
                      rootfs_sha256=hashlib.sha256(modified).hexdigest(),
                      injected_files=manifest, compatible_boards=info['boards'],
                      stock_app_version=locks[device]['app_version'],
                      validation={'container_sha1': 'pass', 'ext_filesystem': 'pass',
                                  'injected_files': 'pass', 'vendor_verifier': 'pending external check',
                                  'hardware_flash_boot_runtime': 'NOT TESTED'},
                      signature_status=info['signatures'], metadata_epoch=EPOCH)
        output.write_bytes(final)
        output.with_suffix('.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
        output.with_suffix('.sha256').write_text(report['output_sha256'] + '  ' + output.name + '\n')
        return report
