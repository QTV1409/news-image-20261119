#!/usr/bin/env python3
"""Entrypoint for the news-image-20261119 entry.

Copies the finished front page (entry.png, drawn by render.py from the
day's verified reporting) to the grader's output directory. Standard
library only, no network, deterministic: the same input bytes are
written on every run.
"""
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "entry.png"
MAX_BYTES = 1048576
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def main():
    data = SRC.read_bytes()
    if data[:8] != PNG_MAGIC:
        raise SystemExit("entry.png is not a PNG file")
    if len(data) > MAX_BYTES:
        raise SystemExit("entry.png is %d bytes, over the 1 MiB limit" % len(data))
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "entry.png"
    shutil.copyfile(SRC, dest)
    print("wrote %s (%d bytes)" % (dest, len(data)))


if __name__ == "__main__":
    main()
