"""Niewielki zapis AVI z bezstratnymi klatkami PNG, bez dodatkowych pakietów."""
import struct
import zlib


def chunk(tag, data):
    return tag + struct.pack('<I', len(data)) + data + (b'\0' if len(data) % 2 else b'')


def png(frame):
    height, width, _ = frame.shape
    def part(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data))
    raw = b''.join(b'\0' + frame[y].tobytes() for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + part(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + part(b'IDAT', zlib.compress(raw, 1)) + part(b'IEND', b''))


class Video:
    def __init__(self, path, width, height, fps=35):
        self.file = open(path, 'w+b')
        self.width, self.height, self.fps = width, height, fps
        self.frames = []
        self.file.write(b'RIFF\0\0\0\0AVI ')
        self.header_pos = self.file.tell()
        self.file.write(self.header(0))
        self.movi_pos = self.file.tell()
        self.file.write(b'LIST\0\0\0\0movi')

    def header(self, count):
        w, h, fps = self.width, self.height, self.fps
        avih = struct.pack('<14I', 1000000 // fps, 0, 0, 0x10, count, 0, 1, w*h*3, w, h, 0, 0, 0, 0)
        strh = struct.pack('<4s4sIHH8I4h', b'vids', b'MPNG', 0, 0, 0, 0, 1, fps, 0, count, w*h*3, 0xffffffff, 0, 0, 0, w, h)
        strf = struct.pack('<IiiHH4sIiiII', 40, w, h, 1, 24, b'MPNG', w*h*3, 0, 0, 0, 0)
        return chunk(b'LIST', b'hdrl' + chunk(b'avih', avih) + chunk(b'LIST', b'strl' + chunk(b'strh', strh) + chunk(b'strf', strf)))

    def write(self, frame):
        data = png(frame)
        offset = self.file.tell() - (self.movi_pos + 8)
        self.file.write(chunk(b'00dc', data))
        self.frames.append((offset, len(data)))

    def close(self):
        f = self.file
        end = f.tell()
        f.seek(self.movi_pos + 4)
        f.write(struct.pack('<I', end - self.movi_pos - 8))
        f.seek(end)
        f.write(chunk(b'idx1', b''.join(struct.pack('<4sIII', b'00dc', 0x10, offset, size) for offset, size in self.frames)))
        end = f.tell()
        f.seek(4)
        f.write(struct.pack('<I', end - 8))
        f.seek(self.header_pos)
        f.write(self.header(len(self.frames)))
        f.close()
