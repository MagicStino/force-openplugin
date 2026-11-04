import struct
import unittest
from openplugin.track_limits import PREDICATE, locate_sites, patch_app

def elf(offset=256, copies=1, flags=5, signature=PREDICATE):
 data=bytearray(offset+copies*len(signature)+32)
 data[:7]=b'\x7fELF\x01\x01\x01'
 struct.pack_into('<H',data,18,40)
 struct.pack_into('<I',data,28,52)
 struct.pack_into('<HH',data,42,32,1)
 struct.pack_into('<8I',data,52,1,offset,0x10000,0,copies*len(signature),copies*len(signature),flags,4)
 data[offset:offset+copies*len(signature)]=signature*copies
 return bytes(data)

class TrackLimitSafety(unittest.TestCase):
 def test_relocated_code_is_found_without_fixed_address(self):
  for offset in [256,4096,8192]:
   sites=locate_sites(elf(offset))
   self.assertEqual(sites['plugin'],offset+0x44)
   self.assertEqual(sites['audio'],offset+0x6c)
   self.assertEqual(sites['virtual_address'],0x10000)
 def test_ambiguous_changed_nonexecutable_truncated_rejected(self):
  for data in [elf(copies=2),elf(flags=4),elf(signature=PREDICATE[:-1]+b'\0'),elf()[:80],b'bad']:
   with self.assertRaises(ValueError):locate_sites(data)
 def test_matching_unknown_firmware_still_rejected(self):
  for device in ['force','mpc-gen1']:
   with self.assertRaisesRegex(ValueError,'Unknown application'):patch_app(elf(),device)
