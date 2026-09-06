#!/usr/bin/env python3
"""Find PS2 games that still need a No-Interlacing patch.

Reads a PCSX2 installation's bundled patch database and game index, and writes
three TSV tables into an output directory:

  deinterlace-coverage.tsv   every NTSC-U / NTSC-J / NTSC-K serial with its
                             deinterlacing status and the patch groups it
                             already has; demo, kiosk, beta and other promo
                             discs are left out (see is_demo)
  cross-region-gaps.tsv      titles where one region or revision already has a
                             deinterlacing patch and an NTSC sibling does not
  fieldrender-gaps.tsv       (needs --upscale-survey) NTSC-U serials measured as
                             true field renderers that have no deinterlacing patch

Usage:

    python tools/scan_deinterlace_coverage.py \
        --pcsx2 "%USERPROFILE%/scoop/apps/pcsx2/current" \
        --out docs/deinterlace/data

    # add the measured field-render join
    python tools/scan_deinterlace_coverage.py \
        --pcsx2 ... --out docs/deinterlace/data \
        --upscale-survey path/to/survey.md

The upscale survey is the community "games tested (upscale without patches)"
list -- a plain-text file of `* Title (REGION)` lines each followed by lines of
the form `640x448 (Before) -> 1280x896 (After)`. It is not redistributed here;
point at your own copy. See docs/deinterlace/no-interlacing-candidates.md
for what the two measurements mean.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import zipfile
from collections import defaultdict

# Patch groups that mean "this game's interlacing is already dealt with".
# Deliberately broad: the official database is not consistent about naming, and
# searching for the literal string "[No-Interlacing]" misses 17 solved games
# (Full Frame Mode, Start in Progressive Mode, Autoboot in 480p, ...).
DEINTERLACE_GROUP = re.compile(r"interlac|progressive|480p|full ?frame", re.I)

# ...but those keywords also appear in unrelated groups.
NOT_DEINTERLACE = re.compile(r"depth of field|softlock", re.I)

# GameIndex.yaml is read line by line. Any non-comment line that starts in
# column 0 opens a new block; only keys that look like a serial are kept.
SERIAL_LINE = re.compile(r"^([A-Z]{4}-\d{5}):")
BLOCK_START = re.compile(r"^[^\s#]")
# `  name: "Title" # comment` -- the value is group 2 when quoted, group 3
# when bare, and a trailing YAML comment is never part of it.
FIELD_LINE = re.compile(r'^  (name|name-en|region):\s*(?:"([^"]*)"|([^#]*?))\s*(?:#.*)?$')
GROUP_LINE = re.compile(r"^\[(.+?)\]", re.M)
NTSC_REGIONS = ("NTSC-U", "NTSC-J", "NTSC-K")

# Demo, kiosk, beta, trial and in-store promo discs are not release builds
# worth patching, and there are enough of them (about one NTSC-U serial in
# six) to swamp the "no pnach at all" rows. SLUS-28xxx / SLUS-29xxx is the
# US third-party demo and public-beta range. NTSC-J names say 体験版 (trial
# version) or 店頭 (in-store), and their name-en says Trial or Demo.
DEMO_SERIAL = re.compile(r"^SLUS-2[89]\d{3}$")
DEMO_NAME = re.compile(
    r"\bdemo\b|kiosk|taikenban|\bbeta\b|\btrial\b|\bpreview\b"
    r"|playstation underground|体験版|店頭",
    re.I,
)


def is_deinterlace(group: str) -> bool:
    return bool(DEINTERLACE_GROUP.search(group)) and not NOT_DEINTERLACE.search(group)


def is_demo(serial: str, entry: dict[str, str]) -> bool:
    """A demo, kiosk, beta or promo disc: not a build anyone will patch."""
    if DEMO_SERIAL.match(serial):
        return True
    return any(DEMO_NAME.search(entry.get(key, "")) for key in ("name", "name-en"))


def read_game_index(path: str) -> dict[str, dict[str, str]]:
    """Parse GameIndex.yaml into {serial: {name, name-en, region}} without a
    YAML dep.

    Three traps in the 2.8.1 file. A few keys do not look like serials
    (SLUS-20643BD, SLUS-21782B, ALCH-0004, PKP2-00702); unless every column-0
    key ends the previous block, their fields land on the entry before them,
    which is how SoulCalibur II came out as a demo disc. About 250 values
    carry a trailing YAML comment. And should a block ever repeat a field,
    the first value wins."""
    entries: dict[str, dict[str, str]] = {}
    current = None
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if BLOCK_START.match(line):
                match = SERIAL_LINE.match(line)
                current = match.group(1) if match else None
                if current:
                    entries[current] = {}
                continue
            if not current:
                continue
            field = FIELD_LINE.match(line)
            if field and field.group(1) not in entries[current]:
                quoted, bare = field.group(2), field.group(3)
                entries[current][field.group(1)] = quoted if quoted is not None else bare
    return entries


def read_patch_groups(
    patches_zip: str, loose_dirs: list[str]
) -> tuple[dict[str, set[str]], int]:
    """Return ({SERIAL_CRC: {group name, ...}}, files read) from patches.zip
    plus any loose .pnach files, which take precedence over the bundle.

    Files whose group headers are all commented out contribute no groups, which
    is correct: a disabled hack is not a patch. In the 2.8.1 bundle 32 files are
    like this, and none of them carry a live patch= line."""
    groups: dict[str, set[str]] = defaultdict(set)
    files_read = 0

    def ingest(stem: str, text: str) -> None:
        for group in GROUP_LINE.findall(text):
            groups[stem].add(group.strip())

    with zipfile.ZipFile(patches_zip) as archive:
        for info in archive.infolist():
            if not info.filename.lower().endswith(".pnach"):
                continue
            stem = os.path.basename(info.filename)[: -len(".pnach")]
            ingest(stem, archive.read(info).decode("utf-8", "replace"))
            files_read += 1

    for directory in loose_dirs:
        for path in glob.glob(os.path.join(directory, "*.pnach")):
            stem = os.path.basename(path)[: -len(".pnach")]
            with open(path, encoding="utf-8", errors="replace") as handle:
                ingest(stem, handle.read())
            files_read += 1

    return groups, files_read


def by_serial(groups: dict[str, set[str]]) -> dict[str, set[str]]:
    """Collapse SERIAL_CRC keys to SERIAL, unioning the groups."""
    merged: dict[str, set[str]] = defaultdict(set)
    for stem, names in groups.items():
        merged[stem.split("_")[0]].update(names)
    return merged


def normalise_title(name: str) -> str:
    name = name.lower()
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\((ntsc[-a-z]*|pal[-a-z]*)\)", "", name)
    name = re.sub(r"[^a-z0-9]+", " ", name).strip()
    return re.sub(r"^(the|a) ", "", name)


def write_tsv(path: str, header: list[str], rows: list[list[str]]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\t".join(header) + "\n")
        for row in rows:
            handle.write("\t".join(row) + "\n")
    print(f"  {os.path.relpath(path):<44} {len(rows):>5} rows")


def emit_coverage(index, serial_groups, out_dir) -> list[list[str]]:
    rows = []
    for serial, entry in sorted(index.items(), key=lambda kv: kv[1].get("name", "")):
        if entry.get("region") not in NTSC_REGIONS or is_demo(serial, entry):
            continue
        groups = serial_groups.get(serial, set())
        solved = sorted(g for g in groups if is_deinterlace(g))
        rows.append([
            entry.get("name", "?"),
            serial,
            entry.get("region", "?"),
            "DEINTERLACE:" + "/".join(solved) if solved else "NO-DEINTERLACE-PATCH",
            "; ".join(sorted(groups)) if groups else "no pnach at all",
        ])
    write_tsv(
        os.path.join(out_dir, "deinterlace-coverage.tsv"),
        ["TITLE", "SERIAL", "REGION", "DEINTERLACE_STATUS", "ALL_EXISTING_GROUPS"],
        rows,
    )
    return rows


def emit_cross_region(index, serial_groups, out_dir) -> None:
    def solved(serial: str) -> bool:
        return any(is_deinterlace(g) for g in serial_groups.get(serial, ()))

    # A patched demo is still a donor, so demos stay on the "have" side; an
    # unpatched one is not a gap, and neither should name the family.
    demos = {serial for serial, entry in index.items() if is_demo(serial, entry)}
    families: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for serial, entry in index.items():
        families[normalise_title(entry.get("name", ""))].append(
            (serial, entry.get("region", "?"), entry.get("name", "?"))
        )

    rows = []
    for key, members in families.items():
        # A title that is all kana, hangul or hanzi normalises to its ASCII
        # residue ("3", "z", ""), which would group unrelated games.
        if len(key) < 3 or not re.search(r"[a-z]", key):
            continue
        have = [m for m in members if solved(m[0])]
        missing = [
            m for m in members
            if not solved(m[0]) and m[1] in NTSC_REGIONS and m[0] not in demos
        ]
        if not have or not missing:
            continue
        rows.append([
            next((m[2] for m in members if m[0] not in demos), members[0][2]),
            "; ".join(f"{s}({r})" for s, r, _ in have),
            "; ".join(f"{s}({r})" for s, r, _ in missing),
        ])
    rows.sort()
    write_tsv(
        os.path.join(out_dir, "cross-region-gaps.tsv"),
        ["TITLE", "PATCHED_SIBLING_SERIALS", "UNPATCHED_NTSC_SERIALS"],
        rows,
    )


def parse_upscale_survey(path: str) -> dict[str, list[str]]:
    measurements: dict[str, list[str]] = {}
    current = None
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            entry = re.match(r"^\*\s+(.*?)\s*$", line)
            if entry:
                current = entry.group(1)
                measurements[current] = []
            elif current and "->" in line:
                measurements[current].append(line.strip())
    return measurements


def classify(lines: list[str]) -> tuple[str, str]:
    """A frame renderer's vertical resolution doubles under 2x upscale; a field
    renderer's does not. Returns (verdict, the measurement line it came from)."""
    for line in lines:
        match = re.search(r"(\d+)x(\d+)\s*\(Before[^)]*\)\s*->\s*(\d+)x(\d+)", line)
        if not match:
            continue
        before, after = int(match.group(2)), int(match.group(4))
        if after >= 2 * before - 2:
            return "frame", line
        if after <= before + 8:
            return "field", line
    return "unclear", lines[0] if lines else ""


def emit_field_render(coverage_rows, survey_path, out_dir) -> None:
    survey = parse_upscale_survey(survey_path)
    lookup: dict[str, list[list[str]]] = defaultdict(list)
    for row in coverage_rows:
        if row[2] == "NTSC-U":
            lookup[normalise_title(row[0])].append(row)

    # Demo discs, betas and reprints are not separate builds worth patching.
    excluded = re.compile(
        r"\[(demo|trade demo|regular demo|greatest hits|online public beta|"
        r"ps underground|cinematic)",
        re.I,
    )

    rows, seen = [], set()
    for title, lines in survey.items():
        verdict, evidence = classify(lines)
        if verdict != "field":
            continue
        for row in lookup.get(normalise_title(title), []):
            if row[3].startswith("DEINTERLACE") or row[1] in seen:
                continue
            if excluded.search(row[0]):
                continue
            seen.add(row[1])
            rows.append([row[0], row[1], row[4], evidence])
    rows.sort()
    write_tsv(
        os.path.join(out_dir, "fieldrender-gaps.tsv"),
        ["TITLE", "SERIAL", "EXISTING_GROUPS", "MEASUREMENT"],
        rows,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--pcsx2",
        required=True,
        help="PCSX2 install directory (the one containing resources/patches.zip)",
    )
    parser.add_argument("--out", default="docs/deinterlace/data", help="output directory")
    parser.add_argument(
        "--upscale-survey",
        help="community upscale survey, to emit fieldrender-gaps.tsv as well",
    )
    args = parser.parse_args()

    resources = os.path.join(args.pcsx2, "resources")
    patches_zip = os.path.join(resources, "patches.zip")
    game_index = os.path.join(resources, "GameIndex.yaml")
    for path in (patches_zip, game_index):
        if not os.path.isfile(path):
            print(f"error: {path} not found -- is --pcsx2 the install root?", file=sys.stderr)
            return 1

    index = read_game_index(game_index)
    groups, files_read = read_patch_groups(
        patches_zip,
        [os.path.join(args.pcsx2, "patches"), os.path.join(args.pcsx2, "cheats_ws")],
    )
    serial_groups = by_serial(groups)

    solved = {s for s, g in serial_groups.items() if any(is_deinterlace(x) for x in g)}
    demos = sum(
        1 for s, e in index.items() if e.get("region") in NTSC_REGIONS and is_demo(s, e)
    )
    print(
        f"{len(index)} serials indexed, {files_read} pnach files, "
        f"{len(solved)} serials already deinterlaced, "
        f"{demos} NTSC demo/promo discs left out of the tables"
    )

    coverage = emit_coverage(index, serial_groups, args.out)
    emit_cross_region(index, serial_groups, args.out)
    if args.upscale_survey:
        emit_field_render(coverage, args.upscale_survey, args.out)
    else:
        print("  (skipped fieldrender-gaps.tsv -- pass --upscale-survey to build it)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
