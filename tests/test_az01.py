import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openplugin.az01 import parse, pack, extract

class AZ01Tests(unittest.TestCase):
    def setUp(self):
        self.root = bytearray(2048)
        self.root[1080:1082] = b'\x53\xef'
        self.info = dict(boards=['inmusic,ada2'], devices=[166215744], description='Test firmware')

    def test_roundtrip_and_repeatability(self):
        a = pack(self.info, self.root, '3.9.1.3-openplugin')
        self.assertEqual(a, pack(self.info, self.root, '3.9.1.3-openplugin'))
        info, root = extract(a)
        self.assertEqual(root, self.root)
        self.assertEqual(info['boards'], self.info['boards'])
        self.assertEqual(info['devices'], self.info['devices'])
        self.assertEqual(info['version'], '3.9.1.3-openplugin')

    def test_tamper_truncation_and_unknown_trailer_rejected(self):
        data = pack(self.info, self.root, 'dev')
        for bad in [data[:20], data + b'SIGN', data[:-1]]:
            with self.assertRaises(ValueError): parse(bad)
        bad = bytearray(data)
        bad[parse(data)['partition_offset'] + 15] ^= 1
        with self.assertRaisesRegex(ValueError, 'SHA-1'): parse(bad)

    def test_compatibility_list_and_version_lengths(self):
        self.info['boards'] = ['inmusic,acv5', 'inmusic,acva2']
        self.info['devices'] = [1, 2]
        for v in ['a', '1234', 'SNAPSHOT-20260709104848', '3.9.1.3-openplugin']:
            info = parse(pack(self.info, self.root, v))
            self.assertEqual(info['version'], v)
            self.assertEqual(info['boards'], self.info['boards'])

if __name__ == '__main__': unittest.main()
