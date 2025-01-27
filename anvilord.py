"""
Anvilord is a tool for lossless Minecraft world compression.
"""

import os
import argparse
import time
import datetime
import gzip
import json
import zipfile

import zopfli

from __version__ import __version__
import region

def search_for_region_folders(path):
    contents = os.listdir(path)
    regions = []

    for i, j in enumerate(contents):
        temp_path = path + "/" + j
        if os.path.isdir(temp_path):
            if (temp_path.endswith("region")
                or temp_path.endswith("entities")
                or temp_path.endswith("poi")):
                regions.append(temp_path)
            else:
                regions += search_for_region_folders(temp_path)

    return regions


def get_all_files_exclude_region(path):
    contents = os.listdir(path)
    files = []

    for i, j in enumerate(contents):
        temp_path = path + "/" + j

        if os.path.isdir(temp_path):
            if not (temp_path.endswith("region")
                or temp_path.endswith("entities")
                or temp_path.endswith("poi")):
                files += get_all_files_exclude_region(temp_path)
        else:
            files.append(temp_path)

    return files


def recompress_chunk(x):
    x_loc = x % 32
    z_loc = x // 32

    if current_region.chunks[z_loc][x_loc] is None:
        return

    stats.total_chunks += 1

    if (not args.disable_quick_compression
        and current_region.chunks[z_loc][x_loc].calculate_sections() == 1):
        stats.skipped_chunks += 1
        return
    
    if args.verbose:
        print(f"\rRecompressing chunk {z_loc:>2}; {x_loc:>2}...", end="  ")

    if args.zopfli_chunk:
        current_region.chunks[z_loc][x_loc].recompress_chunk_zopfli(compression_scheme_mappings[args.compression_scheme],
                                                                    args.zopfli_iterations,
                                                                    args.zopfli_disable_block_splitting,
                                                                    args.zopfli_block_splitting_max)
    else:
        current_region.chunks[z_loc][x_loc].recompress_chunk(compression_scheme_mappings[args.compression_scheme],
                                                             args.compression_level)

    stats.recompressed_chunks += 1


def region_files_integrity():
    for i, j in enumerate(region_folders):
        files = os.listdir(j)

        for i2, j2 in enumerate(files):
            if j2.endswith(".mca") or j2.endswith(".mcr"):
                path = f"{j}/{j2}"
                try:
                    current_region = region.Region()
                    current_region.read_from_file(path)
                except region.HeadersErrorException:
                    print(f'"{path}" has empty headers.')


def squash_region_file():
    if args.verbose:
        time_rs = time.monotonic()

    source_region_sections     = 0
    compressed_region_sections = 0

    for x in range(1024):
        source_region_sections += calculate_chunk_sections(x)
        recompress_chunk(x)
        compressed_region_sections += calculate_chunk_sections(x)

    if compressed_region_sections < source_region_sections:
        diff = source_region_sections - compressed_region_sections
        print(f"Saved {diff * 4_096} bytes.")
        stats.sections_saved += diff
    elif args.verbose:
        print()

    if args.verbose:
        print("Archiving region file.")

    if not args.disable_datetime_preservation:
        date_time = os.path.getmtime(path)
        date_time = datetime.datetime.fromtimestamp(date_time).timetuple()
        infoobj = zopfli.ZipInfo(path, date_time=date_time)
    else:
        infoobj = zopfli.ZipInfo(path)

    # This forces Zopfli to compress files instead of storing them.
    infoobj.compress_type = 8

    arc.writestr(infoobj,
                 current_region.compile_region_file(),
                 compress_type=zipfile.ZIP_DEFLATED,
                 compresslevel=args.compression_level)

    if args.verbose:
        time_re = time.monotonic()
        print(f"Time elapsed: {display_time(time_re - time_rs)}")


def write_everything_but_region():
    for i, path in enumerate(files):
        gzipped = False

        if args.verbose:
            print(f'Packing "{path}"...')

        with open(path, "rb") as f:
            if (not args.disable_gzip_data_recompression
                and not path.endswith(".json")):
                magic = f.read(2)
                f.seek(0)
                d = f.read()
                # Check if current file was gzipped.
                if magic == b"\x1f\x8b":
                    if args.verbose:
                        print("File is gzipped. Recompressing.")
                    gzipped = True
            elif (not args.disable_json_data_minification
                  and path.endswith(".json")):
                d = f.read()

                try:
                    d_jsoned = json.loads(d)
                except json.JSONDecodeError as e:
                    if args.verbose:
                        print(f'Cannot read JSON file: "{e}"')

                d = json.dumps(d_jsoned, separators=(",", ":"))
            else:
                d = f.read()

        if not args.disable_datetime_preservation:
            date_time = os.path.getmtime(path)
            date_time = datetime.datetime.fromtimestamp(date_time).timetuple()
            infoobj = zipfile.ZipInfo(path, date_time=date_time)
        else:
            infoobj = zipfile.ZipInfo(path)

        if gzipped:
            try:
                d_decompressed = gzip.decompress(d)
            except gzip.BadGzipFile as e:
                if args.verbose:
                    print(f'Failed to decompress: "{e}"')
                gzipped = False

        if gzipped and args.zopfli_chunk:
            cobj = zopfli.ZopfliCompressor(zopfli.ZOPFLI_FORMAT_GZIP,
                                           iterations=args.zopfli_iterations,
                                           block_splitting=not args.zopfli_disable_block_splitting,
                                           block_splitting_max=args.zopfli_block_splitting_max)
            d = cobj.compress(d_decompressed) + cobj.flush()
        elif gzipped and not args.zopfli_chunk:
            d = gzip.compress(d_decompressed, compresslevel=args.compression_level)

        # This forces Zopfli to compress files instead of storing them.
        infoobj.compress_type = 8

        arc.writestr(infoobj,
                     d,
                     compress_type=zipfile.ZIP_DEFLATED,
                     compresslevel=args.compression_level)


def calculate_chunk_sections(x):
    x_loc = x % 32
    z_loc = x // 32

    if current_region.chunks[z_loc][x_loc] is None:
        return 0

    return current_region.chunks[z_loc][x_loc].calculate_sections()


def display_time(time):
    hours   = int(time // 3600)
    minutes = int(time % 3600 // 60)
    seconds = int(time % 60)

    return f"{hours:0>2}:{minutes:0>2}:{seconds:0>2}"


class Stats:
    def __init__(self):
        self.total_chunks = 0
        self.skipped_chunks = 0
        self.recompressed_chunks = 0
        self.sections_saved = 0


if __name__ == "__main__":
    compression_scheme_mappings = {"gzip": 1, "zlib": 2, "uncompressed": 3}

    parser = argparse.ArgumentParser(prog="Anvilord",
                                     description="Lossless Minecraft world compression.")
    parser.add_argument("-w", "--world",
                        help="Minecraft world.",
                        required=True)
    parser.add_argument("-o", "--output",
                        help="Minecraft world ZIP file output.",
                        required=True)
    parser.add_argument("-v", "--verbose",
                        help="Enable debug messages.",
                        action="store_true")
    parser.add_argument("--version",
                        action="version",
                        help="Show program's version and exit.",
                        version=f"%(prog)s {__version__}")

    # Groups.
    general = parser.add_argument_group("General")
    compression = parser.add_argument_group("Compression")

    # General.
    general.add_argument("--disable-quick-compression",
                        help="Disable skipping of one-sectioned chunks.",
                        action="store_true")
    general.add_argument("--disable-region-integrity",
                        help="Disable quick region file integrity check.",
                        action="store_true")
    general.add_argument("--disable-datetime-preservation",
                        help="Disable modified datetime preservation.",
                        action="store_true")
    general.add_argument("--disable-gzip-data-recompression",
                        help="Disable recompression of GZip data. (e.g. level data, maps, scoreboards)",
                        action="store_true")
    general.add_argument("--disable-json-data-minification",
                        help="Disable JSON data minification.",
                        action="store_true")

    # Compression.
    compression.add_argument("-s", "--compression-scheme",
                        default="zlib",
                        choices=tuple(compression_scheme_mappings.keys()),
                        help='Override chunk compression scheme. Default: "zlib". Uncompressed is supported for '
                             'Minecraft 1.15.1+ only.')
    compression.add_argument("-c", "--compression-level",
                        type=int,
                        default=9,
                        choices=range(1, 10),
                        help="Set compression level for reference tools. Default: 9.")
    compression.add_argument("--zopfli-chunk",
                        help="Use Zopfli to compress Minecraft chunks. Brutally slower, but more effective.",
                        action="store_true")
    compression.add_argument("--zopfli-gzip",
                        help="Use Zopfli to compress GZip data.",
                        action="store_true")
    compression.add_argument("--zopfli-output",
                        help="Use Zopfli to compress ZIP output.",
                        action="store_true")
    compression.add_argument("--zopfli-iterations",
                        type=int,
                        default=15,
                        help="Set Zopfli iteration count. Default: 15.")
    compression.add_argument("--zopfli-disable-block-splitting",
                        help="Disable Zopfli block splitting.",
                        action="store_false")
    compression.add_argument("--zopfli-block-splitting-max",
                        type=int,
                        default=15,
                        help="Set maximum block splitting. Default: 15.")


    args = parser.parse_args()
    stats = Stats()

    region_folders = search_for_region_folders(args.world)

    if args.disable_region_integrity is False:
        print("Checking region files integrity. This can take some time.")
        region_files_integrity()

    time_s = time.monotonic()

    files = get_all_files_exclude_region(args.world)

    if args.zopfli_output:
        arc = zopfli.ZipFile(args.output, "w")
    else:
        arc = zipfile.ZipFile(args.output, "w")

    print("Packaging non-region files.")
    write_everything_but_region()

    print("Region files squashing started.")

    for i, j in enumerate(region_folders):
        files = os.listdir(j)

        for i2, j2 in enumerate(files):
            valid_region = False
            path = j + "/" + j2

            print(f'Squashing "{path}"...')

            try:
                current_region = region.Region()
                current_region.read_from_file(f"{path}")
                valid_region = True
            except region.HeadersErrorException:
                print(f'"{path}" has empty headers. Skipped.')

            if valid_region:
                squash_region_file()

    time_e = time.monotonic()

    print("Complete! Anvilord carefully recompressed your region files.")
    print()
    print(f"Total chunks:        {stats.total_chunks}")
    print(f"Skipped chunks:      {stats.skipped_chunks}")
    print(f"Compressed chunks:   {stats.recompressed_chunks}")
    print()
    print(f"Bytes saved:         {stats.sections_saved * 4_096}")
    print()
    print(f"Total time elapsed:  {display_time(time_e - time_s)}")