"""Strict AZ01 v1 adapter for the two supplied Gen1 update containers."""
import hashlib
import lzma
import struct


def pad(data, alignment=4):
    return data + b'\0' * (-len(data) % alignment)


def string(value):
    data = value.encode('utf-8')
    return struct.pack('<I', len(data)) + pad(data + b'\0')


class Reader:
    def __init__(self, data, pos=0):
        self.data, self.pos = data, pos

    def take(self, size):
        if size < 0 or self.pos + size > len(self.data):
            raise ValueError('Truncated AZ01 container')
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result

    def integer(self, fmt='<I'):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def text(self):
        size = self.integer()
        if size > 4096:
            raise ValueError('Oversized AZ01 text')
        raw = self.take((size + 4) // 4 * 4)
        if any(raw[size:]):
            raise ValueError('Invalid string terminator/padding')
        return raw[:size].decode('utf-8')


def parse(data):
    r = Reader(data)
    if r.take(4) != b'AZ01' or r.integer() != 1:
        raise ValueError('Only AZ01 version 1 is supported')
    header_end = (r.integer() + 7) // 8 * 8
    version = r.text()
    count = r.integer()
    if not 1 <= count <= 32:
        raise ValueError('Invalid board count')
    boards = [r.text() for _ in range(count)]
    count = r.integer()
    if not 1 <= count <= 32:
        raise ValueError('Invalid device count')
    devices = [r.integer() for _ in range(count)]
    description = r.text()
    if r.pos > header_end or any(data[r.pos:header_end]):
        raise ValueError('Unknown global header fields')
    r.pos = header_end
    start = r.pos
    if r.take(4) != b'PART':
        raise ValueError('Expected one rootfs partition')
    part_end = start + r.integer()
    size = r.integer('<Q')
    name, compression = r.text(), r.text()
    if (name, compression, r.integer()) != ('rootfs', 'xz', 1):
        raise ValueError('Unsupported partition/compression/hash count')
    if r.text() != 'sha1' or r.integer() != 20:
        raise ValueError('Unsupported hash algorithm')
    expected = r.take(20)
    if r.pos != part_end:
        raise ValueError('Unknown partition header fields')
    offset = r.pos
    compressed = r.take(size)
    if hashlib.sha1(compressed).digest() != expected:
        raise ValueError('Rootfs SHA-1 mismatch')
    padding = r.take(-r.pos % 8)
    if any(padding) or r.take(16) != b'EOF\0' + struct.pack('<III', 16, 0, 0) or r.pos != len(data):
        raise ValueError('Extra partitions, signatures or unknown trailer: refuse to rewrite')
    return dict(format='AZ01-v1', version=version, boards=boards, devices=devices,
                description=description, partition_offset=offset, compressed_size=size,
                compressed_sha1=expected.hex(), compressed=compressed,
                signatures='none in supported container; boot policy not validated')


def extract(data):
    info = parse(data)
    decoder = lzma.LZMADecompressor(memlimit=512 * 1024 * 1024)
    rootfs = decoder.decompress(info['compressed'], max_length=1024 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data:
        raise ValueError('Invalid, concatenated or oversized XZ rootfs')
    if rootfs[1080:1082] != b'\x53\xef':
        raise ValueError('Expected ext filesystem')
    return info, rootfs


def pack(info, rootfs, version):
    if not version or len(version) > 64 or '\0' in version:
        raise ValueError('Invalid development version')
    compressed = lzma.compress(rootfs, format=lzma.FORMAT_XZ, check=lzma.CHECK_CRC32, preset=1)
    fields = string(version) + struct.pack('<I', len(info['boards']))
    fields += b''.join(string(board) for board in info['boards'])
    fields += struct.pack('<I', len(info['devices']))
    fields += b''.join(struct.pack('<I', device) for device in info['devices'])
    fields += string(info['description'])
    header = b'AZ01' + struct.pack('<II', 1, 12 + len(fields)) + fields
    header = pad(header, 8)
    part = struct.pack('<Q', len(compressed)) + string('rootfs') + string('xz')
    part += struct.pack('<I', 1) + string('sha1') + struct.pack('<I', 20) + hashlib.sha1(compressed).digest()
    result = pad(header + b'PART' + struct.pack('<I', len(part) + 8) + part + compressed, 8)
    result += b'EOF\0' + struct.pack('<III', 16, 0, 0)
    parse(result)
    return result
