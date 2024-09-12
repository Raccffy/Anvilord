# Anvilord

Anvilord is a tool for lossless Minecraft world compression.

## Features

- Handles a wide range of versions. Starting with Beta 1.3 and ending with the latest snapshot;
- Ability to recompress chunks using [GZip](https://en.wikipedia.org/wiki/Gzip), [zlib](https://en.wikipedia.org/wiki/Zlib) and uncompressed (1.15.1+ only) schemes;
- Includes [Zopfli, state of the art Deflate compression,](https://developers.googleblog.com/en/compress-data-more-densely-with-zopfli) for even smaller world size.

## How?

Region files are basically chunk containers. Every single chunk is compressed in order to save hard disk space. Of course, world saving needs to be done quickly or it will take a very long time.

You **can't** squash region file size using in-game options. Yes, you can [optimize](https://minecraft.wiki/w/World_Options), but this is useful for world updates only. That's why *Anvilord* was created. This iron-clad lord takes region files from your world, smashes them on his trusty anvil, squashes chunks with its strong hands and builds regions back. This process is completely *lossless*.

Using default settings, Anvilord quickly produces output, [that is typically 2 - 6% smaller than the original world size](https://github.com/Raccffy/Anvilord/wiki/Benchmark). With Zopfli compression rate may increase by 1 - 2 %. Better results are achieved with natural world generation, large [Block entity](https://minecraft.wiki/w/Block_entity) data and with tall creations.

## Installation

### Without Python

Download, extract and run binary from [Releases](https://github.com/Raccffy/Anvilord/releases) page. Only Windows 7+ 64-bit builds are avaliable.

### With Python

1. Install Python 3.8 or higher, download project's source code and extract it;
2. Open Terminal, go to the extracted folder and install project requirements: `pip install -r requirements.txt`;
3. Run "anvilord.py".

## Usage

```
usage: Anvilord [-h] -w WORLD -o OUTPUT [-v] [--version] [--disable-quick-compression]
                [--disable-region-integrity] [--disable-datetime-preservation]
                [-s {gzip,zlib,uncompressed}] [-c {1,2,3,4,5,6,7,8,9}] [-z] [--zopfli-output]
                [--zopfli-iterations ZOPFLI_ITERATIONS] [--zopfli-disable-block-splitting]
                [--zopfli-block-splitting-max ZOPFLI_BLOCK_SPLITTING_MAX]

Lossless Minecraft world compression.

optional arguments:
  -h, --help            show this help message and exit
  -w WORLD, --world WORLD
                        Minecraft world.
  -o OUTPUT, --output OUTPUT
                        Minecraft world ZIP file output.
  -v, --verbose         Enable debug messages.
  --version             Show program's version and exit.

General:
  --disable-quick-compression
                        Disable skipping of one-sectioned chunks.
  --disable-region-integrity
                        Disable quick region file integrity check.
  --disable-datetime-preservation
                        Disable modified datetime preservation.

Compression:
  -s {gzip,zlib,uncompressed}, --compression-scheme {gzip,zlib,uncompressed}
                        Override chunk compression scheme. Default: "zlib". Uncompressed is
                        supported for Minecraft 1.15.1+ only.
  -c {1,2,3,4,5,6,7,8,9}, --compression-level {1,2,3,4,5,6,7,8,9}
                        Set compression level for reference tools. Default: 9.
  -z, --zopfli-chunk    Use Zopfli to compress Minecraft chunks. Brutally slower, but more
                        effective.
  --zopfli-output       Use Zopfli to compress ZIP output.
  --zopfli-iterations ZOPFLI_ITERATIONS
                        Set Zopfli iteration count. Default: 15.
  --zopfli-disable-block-splitting
                        Disable Zopfli block splitting.
  --zopfli-block-splitting-max ZOPFLI_BLOCK_SPLITTING_MAX
                        Set maximum block splitting. Default: 15.
```