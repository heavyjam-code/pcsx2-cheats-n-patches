#!/usr/bin/env python3
"""Measure a PS2 game's frame rate by diffing two PCSX2 savestates.

Save a state, wait, save another, and diff the EE RAM image between the two.
Every word that counts frames or vblanks moves by rate x seconds, so the
per-word deltas of a 30 fps game with a 60 Hz vblank pile up in two clusters
in a 2:1 ratio, and a game that already runs at 60 fps gives one dominant
cluster with almost nothing at half of it. docs/60fps/frame-rate-survey.md
explains how to read the result and the two traps (measure in gameplay, and
time the gap around the actual file writes).

Usage:

    python tools/diff_savestates.py FIRST.p2s SECOND.p2s --seconds 9.12

    # gap taken from the two files' modification times instead
    python tools/diff_savestates.py FIRST.p2s SECOND.p2s

Prints how many words changed and increased, the most common increases with
the rate each one implies, and for the 60/s and 30/s rate bands (--bands
50,25 for a PAL game) the number of words inside the band and the first few
of their addresses. Addresses are EE physical (eeMemory.bin is a flat 32 MB
image with a base of 0), so they are the numbers a pnach line or a PINE read
uses.

Needs numpy. A .p2s is a zip archive, and PCSX2 2.x compresses its members
with Zstandard by default (PCSX2.ini: SavestateCompressionType = 2), which
zipfile cannot read before Python 3.14. eeMemory.bin is therefore decoded
with the first of these that works: zipfile itself (stored or deflate
members), the stdlib compression.zstd module (3.14+), the pyzstd or
zstandard package, or a 7-Zip on PATH that understands Zstandard (7-Zip
26.02 does; the 7z command). If none applies, install pyzstd or put 7-Zip
on PATH.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import struct
import subprocess
import sys
import zipfile

import numpy as np

MEMBER = "eeMemory.bin"
ZIP_ZSTD = 93  # zip method id for Zstandard; zipfile knows only 0, 8, 12, 14

# Rate bands the survey reads: the NTSC vblank and half of it. PAL games want
# --bands 50,25 instead; on an NTSC game the PAL bands only collect unrelated
# words that happen to step at those rates.
DEFAULT_BANDS = "60,30"

# PCSX2 names savestates "SERIAL (CRC).slot.p2s".
STATE_NAME = re.compile(r"^([A-Z]{4}-\d{5}) \(([0-9A-Fa-f]{8})\)")


def read_member_raw(path: str, info: zipfile.ZipInfo) -> bytes:
    """Return the still-compressed bytes of one zip member."""
    with open(path, "rb") as f:
        f.seek(info.header_offset)
        header = f.read(30)
        if header[:4] != b"PK\x03\x04":
            raise SystemExit(f"{path}: bad local file header for {info.filename}")
        name_len, extra_len = struct.unpack("<HH", header[26:30])
        f.seek(info.header_offset + 30 + name_len + extra_len)
        return f.read(info.compress_size)


def zstd_decompress(data: bytes, size: int) -> bytes | None:
    """Decompress a Zstandard frame with whichever module is installed."""
    try:
        from compression import zstd  # Python 3.14+

        return zstd.decompress(data)
    except ImportError:
        pass
    try:
        import pyzstd

        return pyzstd.decompress(data)
    except ImportError:
        pass
    try:
        import zstandard

        return zstandard.ZstdDecompressor().decompress(data, max_output_size=size)
    except ImportError:
        pass
    return None


def seven_zip_extract(path: str, member: str) -> bytes | None:
    """Stream one member out of the archive with 7-Zip, or None if there is none."""
    exe = shutil.which("7z") or shutil.which("7zz")
    if not exe:
        return None
    result = subprocess.run([exe, "e", "-so", path, member], capture_output=True)
    if result.returncode != 0:
        message = result.stderr.decode(errors="replace").strip() or f"exit code {result.returncode}"
        raise SystemExit(f"{exe} could not extract {member} from {path}: {message}")
    return result.stdout


def load_ee_memory(path: str) -> bytes:
    with zipfile.ZipFile(path) as z:
        try:
            info = z.getinfo(MEMBER)
        except KeyError:
            raise SystemExit(f"{path}: no {MEMBER} inside; is this a PCSX2 savestate?")
        if info.compress_type in (
            zipfile.ZIP_STORED,
            zipfile.ZIP_DEFLATED,
            zipfile.ZIP_BZIP2,
            zipfile.ZIP_LZMA,
        ):
            return z.read(MEMBER)
    data = None
    if info.compress_type == ZIP_ZSTD:
        data = zstd_decompress(read_member_raw(path, info), info.file_size)
    if data is None:
        data = seven_zip_extract(path, MEMBER)
    if data is None:
        raise SystemExit(
            f"{path}: {MEMBER} uses zip compression method {info.compress_type}, "
            "which this Python cannot read. Install pyzstd (pip install pyzstd), "
            "put 7-Zip on PATH, or set PCSX2's savestate compression to Uncompressed."
        )
    if len(data) != info.file_size:
        raise SystemExit(f"{path}: {MEMBER} decoded to {len(data)} bytes, expected {info.file_size}")
    return data


def state_id(path: str) -> tuple[str, str] | None:
    m = STATE_NAME.match(os.path.basename(path))
    return (m.group(1), m.group(2).upper()) if m else None


def written(path: str) -> str:
    stamp = dt.datetime.fromtimestamp(os.path.getmtime(path))
    return stamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Diff the EE RAM of two PCSX2 savestates and histogram the per-word deltas.",
    )
    ap.add_argument("first", help="the savestate written first")
    ap.add_argument("second", help="the savestate written second")
    ap.add_argument(
        "--seconds",
        type=float,
        help="real seconds between the two savestate writes; default: the "
        "difference between the two files' modification times",
    )
    ap.add_argument(
        "--tolerance",
        type=float,
        default=0.05,
        help="half-width of each rate band as a fraction of its rate (default 0.05, "
        "so the 60/s band is 57-63/s)",
    )
    ap.add_argument(
        "--top",
        type=int,
        default=12,
        help="how many of the most common increases to list (default 12)",
    )
    ap.add_argument(
        "--min-rate",
        type=float,
        default=5.0,
        help="leave increases slower than this many per second out of the top list (default 5)",
    )
    ap.add_argument(
        "--max-rate",
        type=float,
        default=150.0,
        help="leave increases faster than this many per second out of the top list (default 150)",
    )
    ap.add_argument(
        "--max-addrs",
        type=int,
        default=8,
        help="addresses to print per rate band (default 8, 0 for none)",
    )
    ap.add_argument(
        "--bands",
        default=DEFAULT_BANDS,
        help="rates per second to count words around, comma-separated "
        "(default 60,30; use 50,25 for a PAL game)",
    )
    args = ap.parse_args(argv)
    try:
        bands = [float(x) for x in args.bands.split(",") if x.strip()]
    except ValueError:
        raise SystemExit(f"--bands wants comma-separated numbers, not {args.bands!r}")
    if not bands or min(bands) <= 0:
        raise SystemExit("--bands wants one or more positive rates")

    if args.seconds is None:
        seconds = os.path.getmtime(args.second) - os.path.getmtime(args.first)
        source = "from the files' modification times"
        if seconds <= 0:
            raise SystemExit(
                "the second file is not newer than the first: pass the files in the "
                "order they were written, or give the gap with --seconds"
            )
    else:
        seconds = args.seconds
        source = "given with --seconds"
        if seconds <= 0:
            raise SystemExit("--seconds must be positive")

    ids = (state_id(args.first), state_id(args.second))
    if all(ids) and ids[0] != ids[1]:
        print(
            f"warning: the file names say {ids[0][0]} {ids[0][1]} and {ids[1][0]} {ids[1][1]}, "
            "two different games; the deltas below are noise",
            file=sys.stderr,
        )

    a = np.frombuffer(load_ee_memory(args.first), dtype="<u4")
    b = np.frombuffer(load_ee_memory(args.second), dtype="<u4")
    if a.size != b.size:
        raise SystemExit(f"{MEMBER} sizes differ: {a.size * 4} and {b.size * 4} bytes")

    # Unsigned subtraction wraps, so a counter that crossed 2^32 still reads as
    # a small positive step once the result is viewed as signed.
    delta = (b - a).view("<i4")
    changed = int(np.count_nonzero(delta))
    inc_idx = np.flatnonzero(delta > 0)
    inc = delta[inc_idx]

    print(f"first : {args.first}   written {written(args.first)}")
    print(f"second: {args.second}   written {written(args.second)}")
    print(f"gap   : {seconds:.2f} s ({source})")
    print()
    print(f"{a.size} words compared, {changed} changed, {inc.size} increased")
    print()

    rates = inc / seconds
    window = (rates >= args.min_rate) & (rates <= args.max_rate)
    values, counts = np.unique(inc[window], return_counts=True)
    order = np.argsort(-counts, kind="stable")[: args.top]
    print(f"Most common increases between {args.min_rate:g}/s and {args.max_rate:g}/s:")
    print(f"  {'delta':>8} {'words':>8} {'rate/s':>8}")
    if order.size == 0:
        print("  (none)")
    for i in order:
        print(f"  {int(values[i]):>8d} {int(counts[i]):>8d} {values[i] / seconds:>8.1f}")
    print()

    print(f"Rate bands (+/-{args.tolerance * 100:g}%):")
    for rate in bands:
        lo = rate * (1 - args.tolerance) * seconds
        hi = rate * (1 + args.tolerance) * seconds
        mask = (inc >= lo) & (inc <= hi)
        n = int(np.count_nonzero(mask))
        line = f"  {rate:>3.0f}/s {n:>7d} words"
        if n:
            band = inc[mask]
            line += f"   delta {int(band.min())}"
            if band.max() != band.min():
                line += f"-{int(band.max())}"
            if args.max_addrs > 0:
                addrs = inc_idx[mask][: args.max_addrs] * 4
                line += "   " + " ".join(f"{int(x):08X}" for x in addrs)
                if n > args.max_addrs:
                    line += " ..."
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
