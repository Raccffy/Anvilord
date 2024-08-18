# Anvilord

Anvilord is a tool for lossless Minecraft world compression.

## Features

- Handles a wide range of versions. Starting with Beta 1.3 and ending with the latest snapshot;
- Ability to recompress chunks using GZip, zlib and uncompressed (1.15.1+ only) schemes;
- Includes [Zopfli, state of the art Deflate compression,](https://developers.googleblog.com/en/compress-data-more-densely-with-zopfli) for even smaller file size.

## How?

Minecraft region file consists of chunks. Official Minecraft client uses [zlib](https://en.wikipedia.org/wiki/Zlib) for blocks and metadata compression. Of course, it needs to be done quickly or world saving will take a very long time.

You **can't** compress your worlds using higher compression level in-game. That's why *Anvilord* was created. This iron-clad lord takes region files from your world, smashes them on his trusty anvil, squashes chunks with its strong hands and builds regions back. This process is *lossless*. Nothing gets lost.

Using default settings, Anvilord quickly produces output, that is typically 2 - 6% smaller than the original world size. With Zopfli compression rate may increase by 1 - 2 %. Better compression rates are achieved with complex chunks (e.g. Natural world generation, large [Block entity](https://minecraft.wiki/w/Block_entity) data).

## Usage

```
usage: Anvilord [-h] -w WORLD -o OUTPUT [--version]
                [--disable-quick-compression] [--disable-region-integrity]
                [-s {gzip,zlib,uncompressed}] [-c {1,2,3,4,5,6,7,8,9}] [-z]
                [--zopfli-output] [--zopfli-iterations ZOPFLI_ITERATIONS]
                [--zopfli-disable-block-splitting]
                [--zopfli-block-splitting-max ZOPFLI_BLOCK_SPLITTING_MAX]

Lossless recompression of Minecraft region files.

optional arguments:
  -h, --help            show this help message and exit
  -w WORLD, --world WORLD
                        Minecraft world.
  -o OUTPUT, --output OUTPUT
                        Minecraft world ZIP file output.
  --version             Show program's version and exit.

General:
  --disable-quick-compression
                        Disable skipping of one-sectioned chunks.
  --disable-region-integrity
                        Disable quick region file integrity check.

Compression:
  -s {gzip,zlib,uncompressed}, --compression-scheme {gzip,zlib,uncompressed}
                        Override chunk compression scheme. Default: "zlib".
                        Uncompressed is supported for Minecraft 1.15.1+ only.
  -c {1,2,3,4,5,6,7,8,9}, --compression-level {1,2,3,4,5,6,7,8,9}
                        Set compression level for reference tools. Default: 9.
  -z, --zopfli-chunk    Use Zopfli to compress Minecraft chunks. Brutally
                        slower, but more effective.
  --zopfli-output       Use Zopfli to compress ZIP output.
  --zopfli-iterations ZOPFLI_ITERATIONS
                        Set Zopfli iteration count. Default: 15.
  --zopfli-disable-block-splitting
                        Disable Zopfli block splitting.
  --zopfli-block-splitting-max ZOPFLI_BLOCK_SPLITTING_MAX
                        Set maximum block splitting. Default: 15.
```