#!/usr/bin/env python3
"""Prepare photos and videos for the repo.

  process_media.py photo SRC DEST.jpg [--crop LEFT TOP RIGHT BOTTOM]
  process_media.py video SRC DEST.mp4

Photos: upright, optional crop (fractions 0-1 of width/height), max 1600 px, JPEG q80, no metadata (EXIF, GPS).
Videos: H.264 960x540 with macOS avconvert, so they stay under GitHub's 10 MB attachment limit.
"""
import argparse
import os
import subprocess
import sys

MAX_SIDE = 1600
VIDEO_LIMIT = 10_000_000


def photo(src, dest, crop):
    try:
        from PIL import Image, ImageOps
    except ImportError:
        sys.exit("Pillow is missing: pip3 install pillow")
    im = ImageOps.exif_transpose(Image.open(src))
    if crop:
        w, h = im.size
        left, top, right, bottom = crop
        im = im.crop((round(left * w), round(top * h), round(right * w), round(bottom * h)))
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    im.convert("RGB").save(dest, "JPEG", quality=80, optimize=True)  # no exif= argument, so metadata is dropped
    print(f"{dest}: {im.size[0]}x{im.size[1]}, {os.path.getsize(dest) // 1024} KB")


def video(src, dest):
    for preset in ("Preset960x540", "Preset640x480"):
        subprocess.run(["avconvert", "--source", src, "--preset", preset, "--output", dest, "--replace"],
                       check=True, stdout=subprocess.DEVNULL)
        size = os.path.getsize(dest)
        if size < VIDEO_LIMIT:
            print(f"{dest}: {preset}, {size / 1e6:.1f} MB")
            return
    sys.exit(f"{dest} is still {size / 1e6:.1f} MB: trim the clip or upload it to YouTube")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kind", choices=["photo", "video"])
    parser.add_argument("src")
    parser.add_argument("dest")
    parser.add_argument("--crop", nargs=4, type=float, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    args = parser.parse_args()
    if args.kind == "photo":
        photo(args.src, args.dest, args.crop)
    else:
        video(args.src, args.dest)


if __name__ == "__main__":
    main()
