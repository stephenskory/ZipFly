import zlib


class Compressor:
    def __init__(self, file: 'BaseFile'):
        self.file = file

        if file.compression_method == 0:
            self.process = self._process_through
            self.tail = self._no_tail
        elif file.compression_method == 8:  # deflate compression
            self.compr = zlib.compressobj(5, zlib.DEFLATED, -15)
            self.process = self._process_deflate
            self.tail = self._tail_deflate

    # no compression
    def _process_through(self, chunk):
        self.file.add_compressed_size(len(chunk))
        self.file.set_crc(zlib.crc32(chunk, self.file.get_crc()))
        return chunk

    def _no_tail(self):
        return b''

    # deflate compression
    def _process_deflate(self, chunk):
        self.file.set_crc(zlib.crc32(chunk, self.file.get_crc()))
        chunk = self.compr.compress(chunk)
        self.file.add_compressed_size(len(chunk))
        return chunk

    def _tail_deflate(self):
        chunk = self.compr.flush(zlib.Z_FINISH)
        self.file.add_compressed_size(len(chunk))
        return chunk
