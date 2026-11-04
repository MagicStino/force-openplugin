"""Exact-version ARM track-limit patch. No heuristic matching or unknown inputs."""
import hashlib
import struct
CONFIG = {
 'force': {
  'base_sha256': 'b54a39689988bf6550e3e28a8a07231ba9f621da8f82859a94695e72f6725f84',
  'app_sha256': '7bbbd8050bfe67db4d320df0ab39f5c3194210f9bbd225d8415f0c4c5f43300d',
  'patched_sha256': 'bc7fd41b42747dae69857afeb4437f28d74c8a26431c00f7c86c5a82ad4f24f9',
 },
 'mpc-gen1': {
  'base_sha256': 'e6cd0c1491021090067917a9a924d528c8d5bd48616e52207900353e47b2df2c',
  'app_sha256': '753f838ca362d42c8cc3f5c9c3fcc604ba076b5919212e0301923a3c11c93494',
  'patched_sha256': 'eef95ee4e47290c26b7fce78270dd0ae3bf241afc321476cd7808b7c813f329b',
 },
}
# Complete verified allocation predicate, including branches and both comparisons.
# Offsets below are relative to this matched block, never firmware addresses.
PREDICATE = bytes.fromhex(
 "a0c090e5a43090e50c3043e044c090e5433182e00c0053e10d00008a030051e3"
 "0300000a060051e30b00000a0100a0e31eff2fe1201190e5243190e5010043e0"
 "400182e0080050e30000a0830100a0931eff2fe10000a0e31eff2fe1c01090e5"
 "c43090e5013043e0432182e0080052e30000a0830100a0931eff2fe1")
RELATIVE_SITES = {'plugin': 0x44, 'audio': 0x6c}

def locate_sites(data):
 """Require one complete predicate in executable ARM ELF load segments.

 Locating a signature does NOT authorize a new firmware: patch_app additionally
 requires an explicitly reviewed input and output hash profile.
 """
 if len(data) < 52 or data[:7] != b'\x7fELF\x01\x01\x01':
  raise ValueError('Expected little-endian ELF32')
 if struct.unpack_from('<H', data, 18)[0] != 40:
  raise ValueError('Expected ARM application')
 phoff = struct.unpack_from('<I', data, 28)[0]
 phsize, phnum = struct.unpack_from('<HH', data, 42)
 if phsize != 32 or not phnum or phoff + phsize * phnum > len(data):
  raise ValueError('Invalid ELF program headers')
 matches = []
 for i in range(phnum):
  kind, offset, va, _, filesz, memsz, flags, _ = struct.unpack_from('<8I', data, phoff + i * phsize)
  if kind != 1 or not flags & 1:
   continue
  if filesz > memsz or offset + filesz > len(data):
   raise ValueError('Invalid executable segment')
  at = data.find(PREDICATE, offset, offset + filesz)
  while at != -1:
   if (va + at - offset) % 4 == 0:
    matches.append((at, va + at - offset))
   at = data.find(PREDICATE, at + 1, offset + filesz)
 if len(matches) != 1:
  raise ValueError('Expected exactly one verified executable predicate')
 base, va = matches[0]
 return {'predicate': base, 'virtual_address': va,
         **{name: base + relative for name, relative in RELATIVE_SITES.items()}}

def sha(data):
 return hashlib.sha256(data).hexdigest()

def patch_app(data, device):
 cfg = CONFIG[device]
 if sha(data) != cfg['app_sha256']:
  raise ValueError('Unknown application; new firmware needs a validated profile')
 sites = locate_sites(data)
 out = bytearray(data)
 for name, opcode in [('plugin', '080050e3'), ('audio', '080052e3')]:
  off = sites[name]
  if data[off:off+4] != bytes.fromhex(opcode):
   raise ValueError('Instruction mismatch')
  out[off] = 16
 if sha(out) != cfg['patched_sha256']:
  raise ValueError('Unexpected patched hash')
 return bytes(out)
