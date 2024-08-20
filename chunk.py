"""
Library for reading and manipulating chunks.
"""

import gzip
import zlib

import zopfli

# GZip, zlib, uncompressed, LZ4 and custom compression schemes.
valid_compression_schemes = (1, 2, 3, 4, 127,)


class Chunk:
    def __init__(self, x, z, timestamp, data, compression):
        if compression not in valid_compression_schemes:
            raise ValueError(f"Compression scheme {compression} is invalid.")
        elif compression == 127:
            raise RuntimeError("Custom compression algorithms are not supported.")

        self.x = x
        self.z = z
        self.timestamp = timestamp
        self.data = data
        self.compression = compression


    def calculate_sections(self):
        # No math.ceil() involved!
        return -(-len(self.data) // 4096)


    def decompress_chunk(self):
        # GZip-compressed chunk.
        if self.compression == 1:
            data = gzip.decompress(self.data)
        # Zlib-compressed chunk.
        elif self.compression == 2:
            data = zlib.decompress(self.data)
        # Uncompressed.
        elif self.compression == 3:
            pass
        # LZ4-compressed chunk.
        elif self.compression == 4:
            raise NotImplementedError("LZ4 decompression is not implemented.")
        elif self.compression == 127:
            raise RuntimeError("Custom compression algorithms are not supported.")
        else:
            raise RuntimeError(f"Unknown compression scheme {self.compression}.")

        return data


    def recompress_chunk(self, target_compression_type, compression_level):
        data = self.decompress_chunk()

        if target_compression_type == 1:
            res = gzip.compress(data, compresslevel=compression_level)
        elif target_compression_type == 2:
            res = zlib.compress(data, level=compression_level)
        elif target_compression_type == 3:
            res = data
        elif target_compression_type == 4:
            raise NotImplementedError("LZ4 compression is not implemented.")
        elif target_compression_type == 127:
            raise RuntimeError("Custom compression algorithms are not supported.")
        else:
            raise ValueError(f'Unknown compression scheme {target_compression_type}.')

        self.compression = target_compression_type
        self.data = res


    def recompress_chunk_zopfli(self,
                                target_compression_type,
                                iterations=15,
                                block_splitting=True,
                                block_splitting_max=15):
        data = self.decompress_chunk()

        if target_compression_type == 1:
            compression_format = zopfli.ZOPFLI_FORMAT_GZIP
        elif target_compression_type == 2:
            compression_format = zopfli.ZOPFLI_FORMAT_ZLIB
        elif target_compression_type == 3:
            res = data
        elif target_compression_type == 4:
            raise NotImplementedError("LZ4 compression is not implemented.")
        else:
            raise ValueError(f'Unknown compression scheme {target_compression_type}.')

        cobj = zopfli.ZopfliCompressor(compression_format,
                                       iterations=iterations,
                                       block_splitting=block_splitting,
                                       block_splitting_max=block_splitting_max)
        res = cobj.compress(data) + cobj.flush()

        self.compression = target_compression_type
        self.data = res