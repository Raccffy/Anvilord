"""
Library for reading and manipulating Region file format.
"""

import struct

import chunk


class Region:
    def __init__(self):
        self.chunks = self.create_empty_region()

    def create_empty_region(self):
        chunks = {}

        for z in range(0, 32):
            chunks[z] = {}
            for x in range(0, 32):
                chunks[z][x] = None

        return chunks

    def read_from_file(self, filename):
        f = open(filename, "rb")
        d = f.read(8192)

        if len(d) != 8192:
            raise HeadersErrorException(f"Region header must contain 8192 bytes (got {len(d)}).")

        locations  = bytearray(d[:4096])
        timestamps = bytearray(d[4096:8192])

        # Region file can contain up to 1,024 chunks.
        for x in range(1024):
            x_loc = x % 32
            z_loc = x // 32

            # There's no standard 3-byte integer data type, so...
            offset = (  int(locations[4 * x])     * 256 ** 2
                      + int(locations[4 * x + 1]) * 256
                      + int(locations[4 * x + 2]))

            sector_count = int(locations[4 * x + 3])

            if offset != 0:
                f.seek(offset * 4096)
                raw_data = f.read(sector_count * 4096)

                stream_length    = struct.unpack(">I", raw_data[0:4])[0]
                compression_type = struct.unpack("B",  raw_data[4:5])[0]

                nbt_data = raw_data[5:stream_length + 5]

                self.chunks[z_loc][x_loc] = chunk.Chunk(x_loc,
                                                        z_loc,
                                                        timestamps[x * 4:x * 4 + 4],
                                                        nbt_data,
                                                        compression_type)


    def compile_region_file(self):
        result = bytearray(8192)

        for x in range(1024):
            x_loc = x % 32
            z_loc = x // 32

            current_chunk = self.chunks[z_loc][x_loc]

            if current_chunk is not None:
                temp = bytearray()

                section_count  = current_chunk.calculate_sections()
                pointer_offset = self.calculate_chunk_location_offset(x_loc, z_loc)
                chunk_offset   = len(result) // 4096

                if chunk_offset >= 256 ** 3:
                    raise OverflowError(f"Chunk offset is too large. (got {chunk_offset})")
                elif section_count > 255:
                    raise OverflowError(f"Chunk size is too large. (got {section_count} sections)")
                elif pointer_offset > 256 ** 4:
                    raise OverflowError(f"Chunk pointer is too large. (got {pointer_offset})")

                chunk_offset     = struct.pack(">I", chunk_offset)[1:]
                section_count    = struct.pack("B",  section_count)
                compression_type = struct.pack("B",  current_chunk.compression)
                stream_length    = struct.pack(">I", len(current_chunk.data))

                temp += stream_length + compression_type
                temp += current_chunk.data
                temp += bytearray(4096 - ((len(current_chunk.data) + 5) % 4096))

                if len(temp) % 4096 != 0:
                    raise AssertionError("Region file size is not divisible by 4096.")

                result += temp

                result[pointer_offset:pointer_offset + 4] = chunk_offset + section_count
                result[pointer_offset + 4096:pointer_offset + 4096 + 4] = current_chunk.timestamp

        return result


    def __str__(self):
        return self.__repr__()


    def __repr__(self):
        return "Region()"


    def calculate_chunk_location_offset(self, x, z):
        if not (0 <= x < 32):
            raise ValueError("X is out of bounds. Expected: 0 <= x < 32")
        elif not (0 <= z < 32):
            raise ValueError("Z is out of bounds. Expected: 0 <= z < 32")

        return 4 * ((x % 32) + (z % 32) * 32)


class HeadersErrorException(Exception):
    pass