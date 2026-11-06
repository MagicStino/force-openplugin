"""Deterministic, unmounted rootfs injection. No signature or boot-policy patching."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import struct
import tempfile
from .az01 import extract, pack, parse

VERSION = '0.9.0'
CONTAINER_VERSION = '3.10.0-openplugin-v0.9.0'
EPOCH = 1791417600  # 2026-10-08 00:00 UTC, metadata only
ROOT = Path(__file__).resolve().parents[1]


def quote(value):
    value = str(value)
    if any(c in value for c in ['"', '\\', '\n', '\r']):
        raise ValueError('Unsupported debugfs path characters')
    return '"' + value + '"'


def build(image, device, payload, output, tracks16=False):
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
    if info['boards'] != locks[device]['boards'] or info['devices'] != locks[device]['devices']:
        raise ValueError('Stock image device metadata mismatch')
    del source
    if not (payload / 'usr/share/openplugin/VERSION').is_file():
        raise ValueError('Native payload missing: run tools/build_native.py first')
    native = payload / 'usr/share/Akai/Content/Synths/OPENPLUGIN - VST - OpenPlugin Manager/plugin_manager.so'
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
        track_report = None
        if tracks16:
            from .track_limits import patch_app, locate_sites, sha
            app = temp / 'MPC'
            subprocess.run(['debugfs', '-R', f'dump /usr/bin/MPC {quote(app)}', str(fs)], capture_output=True, check=True)
            original = app.read_bytes(); patched = patch_app(original, device)
            sites = locate_sites(original); raw = bytearray(fs.read_bytes())
            blocksize = 1024 << struct.unpack_from('<I', raw, 1048)[0]
            for kind in ('plugin', 'audio'):
                off = sites[kind]; logical, within = divmod(off, blocksize)
                result = subprocess.check_output(['debugfs', '-R', f'bmap /usr/bin/MPC {logical}', str(fs)], stderr=subprocess.DEVNULL, text=True)
                pos = int(result.strip()) * blocksize + within
                if raw[pos:pos+4] != original[off:off+4]: raise ValueError('Track patch block mapping mismatch')
                raw[pos:pos+4] = patched[off:off+4]
            fs.write_bytes(raw); del raw
            subprocess.run(['debugfs', '-R', f'dump /usr/bin/MPC {quote(app)}', str(fs)], capture_output=True, check=True)
            if app.read_bytes() != patched: raise ValueError('Track patch verification failed')
            track_report = {'audio': 16, 'plugin': 16, 'original_app_sha256': sha(original), 'app_sha256': sha(patched)}
        shadow_override = None
        if (payload / 'usr/share/openplugin/authorized_keys').is_file() or (payload / 'usr/share/openplugin/remote-sshd_config').is_file():
            shadow_override = temp / 'shadow'
            subprocess.run(['debugfs', '-R', f'dump /etc/shadow {quote(shadow_override)}', str(fs)], capture_output=True, check=True)
            lines = shadow_override.read_text().splitlines()
            roots = [i for i, line in enumerate(lines) if line.startswith('root:')]
            if len(roots) != 1:
                raise ValueError('Expected exactly one root account')
            fields = lines[roots[0]].split(':')
            # Linux OpenSSH treats ! as an account lock, blocking keys as well.
            # Key-only builds use an unusable password. Shared password builds
            # install the explicitly requested root/mpc hash before boot (rootfs is read-only).
            fields[1] = '*' if (payload / 'usr/share/openplugin/authorized_keys').is_file() else subprocess.check_output(['openssl', 'passwd', '-6', '-salt', 'openplugin07', '-stdin'], input=b'mpc\n').decode().strip()
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
                mode = '0100755' if path.suffix in ('.sh', '.so') or path.name in ('skin-locations', 'locations-tool', 'locations-display') else '0100644'
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
        final = pack(info, modified, CONTAINER_VERSION)
        final_info = parse(final)
        if final_info['boards'] != info['boards'] or final_info['devices'] != info['devices']:
            raise ValueError('Device compatibility changed')
        report = dict(project_version=VERSION, container_version=CONTAINER_VERSION, device=device, input_sha256=source_hash,
                      output_sha256=hashlib.sha256(final).hexdigest(), output_size=len(final),
                      rootfs_sha256=hashlib.sha256(modified).hexdigest(),
                      injected_files=manifest, compatible_boards=info['boards'],
                      stock_app_version=locks[device]['app_version'],
                      validation={'container_sha1': 'pass', 'ext_filesystem': 'pass',
                                  'injected_files': 'pass', 'vendor_verifier': 'pending external check',
                                  'hardware_flash_boot_runtime': 'NOT TESTED'},
                      signature_status=info['signatures'], metadata_epoch=EPOCH, tracks16=track_report)
        output.write_bytes(final)
        output.with_suffix('.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
        output.with_suffix('.sha256').write_text(report['output_sha256'] + '  ' + output.name + '\n')
        return report
