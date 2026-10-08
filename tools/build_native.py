#!/usr/bin/env python3
"""Build the native manager from local source and pinned upstream skin/wrapper."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import io
import tarfile
import re

ROOT = Path(__file__).resolve().parents[1]

def run(*args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, **kwargs)

def normalize_presets(folder):
    for preset in folder.rglob('*.xpl'):
        preset.write_text(re.sub(r'(<version file="1" date=")[^"]+("/>)',
            r'\g<1>2026-10-08-00-00\2',preset.read_text()))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--deps', type=Path, default=ROOT / '.deps')
    p.add_argument('--output', type=Path, default=ROOT / 'build/native')
    p.add_argument('--ssh-key', type=Path, help='Owner public key; private key must never be supplied')
    args = p.parse_args()
    deps, out = args.deps.resolve(), args.output.resolve()
    locks = json.loads((ROOT / 'dependencies.json').read_text())
    for name, lock in locks.items():
        actual = subprocess.check_output(['git', '-C', str(deps / name), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != lock['commit']:
            p.error(f'{name} must be at {lock["commit"]}; got {actual}')
    # Build committed trees, so uncommitted files in a dependency cannot alter an image.
    pinned = out / 'dependencies'
    if pinned.exists():
        shutil.rmtree(pinned)
    for name, lock in locks.items():
        dest = pinned / name
        dest.mkdir(parents=True)
        archive = subprocess.check_output(['git','-C',str(deps/name),'archive',lock['commit']])
        with tarfile.open(fileobj=io.BytesIO(archive)) as files:
            files.extractall(dest, filter='data')
    mv = pinned / 'mpc-vst-plugins'
    manager = pinned / 'mpc-vst-manager'
    # A fresh source copy avoids modifying either dependency checkout.
    local = out / 'source'
    if local.exists():
        shutil.rmtree(local)
    shutil.copytree(manager / 'vst', local / 'vst', ignore=shutil.ignore_patterns('build', '__pycache__'))
    layout = local / 'vst/layout.conf'
    spec = local / 'vst/vst.json'
    config = json.loads(spec.read_text())
    config['defines']['PARAM_TEXT_MAX'] = 192
    spec.write_text(json.dumps(config, indent=2) + '\n')
    layout.write_text(layout.read_text().replace('[tab PLUGINS]','[tab CATALOG]').replace('qlinks "PLUGINS"','qlinks "CATALOG"').replace('sw=146 sh=44 key=kind','sw=100 sh=44 key=kind options="All,Instr.,Effects,Trackers,Samplers,Tools"').replace(
        'button cx=578 cy=178 label="" key=noop img=images/upd_badge.svg w=24 h=24 when=upd_badge:on',
        'art file=images/upd_badge.svg x=566 y=166 w=24 h=24 when=upd_badge:on'))
    images = local / 'vst/make_images.py'
    images.write_text(images.read_text().replace('"PLUGIN MANAGER", 24', '"OPENPLUGIN", 24')
        .replace('spacing=3)', 'spacing=3) + text(300, 39, "COMMUNITY INSTRUMENTS & PLUGINS", 16, MUTED, 600)')
        .replace('"APPLY",','"CONTINUE",').replace('"RESTART & APPLY",','"INSTALL & RESTART",'))
    run(sys.executable, images)
    run(sys.executable, ROOT / "tools/build_previews.py", "--output", local / "vst/images/previews")
    for name in ['card_off.svg','card_on.svg']:
        card=local/'vst/images'/name
        card.write_text(re.sub(r'<rect x="13"[^>]+/>','',card.read_text()))
    from customize_skin import customize
    customize(local / 'vst')
    run(sys.executable, ROOT / 'tools/generate_skin.py', mv, local / 'vst/vst.json')
    # The generator groups artwork before controls; move preview overlays after
    # row backgrounds so opaque card art cannot hide the plugin screenshots.
    tui=local/'vst/build/skin/poloq - VST - Plugin Manager/Plugin Skins/TUI.json'
    ui=json.loads(tui.read_text())
    preview_params={f'Parameter {i}' for i,p in enumerate(json.loads((local/'vst/params.json').read_text())['params']) if p['key'].endswith('_preview')}
    for definition in ui['pageData']['componentDefinitions']['localComponentDefinitions']:
        if definition['key']!='CATALOG|CATALOG': continue
        nodes=definition['value']['componentsData']
        def preview_node(node):
            return any(h.startswith('IndexedEnabling/') and h.split('/',3)[-1] in preview_params for h in node['bounds'].get('additionalInvalidatingHandles',[]))
        previews=[node for node in nodes if preview_node(node)]
        definition['value']['componentsData']=[node for node in nodes if not preview_node(node)]+previews
    tui.write_text(json.dumps(ui,indent=2)+'\n')
    import ziglang
    zig = Path(ziglang.__file__).parent / 'zig'
    env = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=str(out / 'zig-global'), ZIG_LOCAL_CACHE_DIR=str(out / 'zig-local'))
    binary = out / 'plugin_manager.so'
    run(zig, 'cc', '-target', 'arm-linux-gnueabihf.2.31', '-mcpu=cortex_a17', '-O2', '-g0', '-s',
        '-fPIC', '-shared', '-fvisibility=hidden', '-std=gnu11', '-I' + str(local / 'vst/build'),
        ROOT / 'native/manager.c', mv / 'wrapper/vst2_wrap.c', '-lpthread', '-ldl', '-lm',
        '-Wl,--no-undefined', '-o', binary, env=env)
    payload = out / 'payload'
    if payload.exists():
        shutil.rmtree(payload)
    synths = payload / 'usr/share/Akai/Content/Synths'
    folder = synths / 'poloq - VST - Plugin Manager'
    shutil.copytree(local / 'vst/build/skin/poloq - VST - Plugin Manager', folder)
    normalize_presets(folder)
    shutil.copyfile(binary, folder / 'plugin_manager.so')
    entry = (local / 'vst/build/pluginlist-entry.xml').read_text().replace('/sdcard/Synths', '%payload-path%')
    (folder / 'plugin-meta.xml').write_text(entry)
    helpers = payload / 'usr/share/openplugin'
    helpers.mkdir(parents=True)
    for name in ['sync.sh', 'plugin_list.awk']:
        shutil.copyfile(mv / 'tools/release' / name, helpers / name)
    for name in ['register.sh']:
        shutil.copyfile(ROOT / 'runtime' / name, helpers / name)
    units = payload / 'usr/lib/systemd/system'
    units.mkdir(parents=True)
    shutil.copyfile(ROOT / 'runtime/openplugin-register.service', units / 'openplugin-register.service')
    enabled = payload / 'etc/systemd/system/multi-user.target.wants'
    enabled.mkdir(parents=True)
    (enabled / 'openplugin-register.service').symlink_to('/usr/lib/systemd/system/openplugin-register.service')
    (helpers / 'VERSION').write_text('3.9.1.4-openplugin\n')
    shutil.copyfile(ROOT / 'assets/previews.lock.json', helpers / 'previews.lock.json')
    (helpers / 'dependencies.json').write_text(json.dumps(locks, indent=2) + '\n')
    for src, dest in [(ROOT / 'native/LICENSE', 'MANAGER-LICENSE'), (mv / 'LICENSE', 'WRAPPER-LICENSE'),
                      (mv / 'tools/html_art/fonts/OFL.txt', 'FONT-OFL'), (ROOT / 'native/NOTICE.md', 'NOTICE.md')]:
        shutil.copyfile(src, helpers / dest)
    if args.ssh_key:
        key = args.ssh_key.read_text().strip()
        if not key.startswith('ssh-ed25519 ') or len(key.splitlines()) != 1:
            p.error('Supply exactly one Ed25519 PUBLIC key')
        run('ssh-keygen', '-l', '-f', args.ssh_key)
        (helpers / 'authorized_keys').write_text(key + '\n')
        for name in ['ssh-prepare.sh', 'sshd_config']:
            shutil.copyfile(ROOT / 'runtime' / name, helpers / name)
        shutil.copyfile(ROOT / 'runtime/openplugin-ssh.service', units / 'openplugin-ssh.service')
        (enabled / 'openplugin-ssh.service').symlink_to('/usr/lib/systemd/system/openplugin-ssh.service')
    print('Native payload:', payload)

if __name__ == '__main__':
    main()
