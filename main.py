#!/usr/bin/env python3
"""Entry program for the news-image-20261119 competition.

Copies the bundled entry.png to the output directory, byte for byte.
The image is validated before the copy (PNG signature, IHDR dimensions
within 1024x1024, file size within 1 MiB) and the written file is read
back and compared with the source, so a run only succeeds when the
output is an exact copy of the shipped image.

Standard library only. The output directory comes from the
MAKEFUN_OUTPUT_DIR environment variable, defaulting to /output.
"""

import os
import sys

MAX_BYTES = 1048576  # 1 MiB
MAX_DIM = 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print("error: " + message, file=sys.stderr)
    return 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    if not os.path.isfile(source):
        return fail("entry.png not found next to main.py at " + source)

    with open(source, "rb") as handle:
        data = handle.read()

    if len(data) > MAX_BYTES:
        return fail("entry.png is %d bytes, over the 1 MiB limit" % len(data))
    if len(data) < 24 or not data.startswith(PNG_SIGNATURE):
        return fail("entry.png does not start with a PNG signature")
    if data[12:16] != b"IHDR":
        return fail("entry.png has no IHDR chunk where one is required")
    # A whole PNG ends with the empty IEND chunk: a zero length, the
    # chunk name and its fixed CRC. Anything else means the file was
    # truncated, which the gate would reject, so refuse to ship it.
    iend_tail = b"\x00\x00\x00\x00IEND\xae\x42\x60\x82"
    if not data.endswith(iend_tail):
        return fail("entry.png does not end with an IEND chunk; file looks truncated")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width < 1 or height < 1:
        return fail("entry.png declares an empty image (%dx%d)" % (width, height))
    if width > MAX_DIM or height > MAX_DIM:
        return fail(
            "entry.png is %dx%d, over the %d pixel limit" % (width, height, MAX_DIM)
        )

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        return fail("cannot create output directory %s: %s" % (out_dir, exc))
    target = os.path.join(out_dir, "entry.png")
    try:
        with open(target, "wb") as handle:
            handle.write(data)
    except OSError as exc:
        return fail("cannot write %s: %s" % (target, exc))

    try:
        with open(target, "rb") as handle:
            written = handle.read()
    except OSError as exc:
        return fail("cannot read back %s: %s" % (target, exc))
    if written != data:
        return fail("written file differs from entry.png; copy is not exact")

    print("wrote %s (%d bytes, %dx%d)" % (target, len(written), width, height))
    return 0


if __name__ == "__main__":
    sys.exit(main())
