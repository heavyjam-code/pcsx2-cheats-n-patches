# AGENTS.md

Hand-made PCSX2 `.pnach` patches. File format reference: `docs/pnach-format.md`.
Start new patches from `templates/template.pnach`.

At the start of a session, also read `Codex.local.md` if it exists. It holds
machine-specific paths and notes and is gitignored; keep shared rules here.

## Never put `//` comments in a `.pnach` file

A finished patch file contains only these keys:

```
gametitle=   [Group]   author=   description=   gsinterlacemode=   patch=
```

No header block, no per-address annotations, no explanatory note above or
beside a `patch=` line. Not even one. If a `.pnach` in `patches/` has a `//` in
it, that is a bug to fix, not a style to match.

This is a rule about which file the writing goes in, not about being terse:

| What you want to record | Where it goes |
|---|---|
| What the patch does and what it costs — the text PCSX2 shows in the Patches tab | `description=` in that group |
| Addresses, disassembly, why each value, what was tried and ruled out | `docs/<category>/devlog-SERIAL-<slug>.md` |

`<category>` is one of `deinterlace`, `deblur`, `60fps` or `misc` — the same
split the `docs/` tree uses. A patch whose file spans two categories (Ys VI
ships both `[60 FPS]` and `[No-Interlacing]`) gets one devlog per category,
cross-linked, not one devlog filed under whichever came first.

So: explain generously, just not in the `.pnach`. When you catch yourself about
to write `// same builder, NTSC FRAME path: DH = height-1`, that sentence is a
devlog sentence. The patch file is the six lines that survive after the
reasoning has been written down somewhere a reader can follow it.

`description=` is the one place a `.pnach` should read like prose — it is
user-facing, and for a file with two mutually exclusive groups it is how
someone picks between them. Write it properly.

## Other conventions

- One file per release, named `SERIAL_CRC.pnach`. Addresses differ between
  regions and revisions — never rename a file to cover another build.
- `[Widescreen 16:9]` and `[No-Interlacing]` must be spelled exactly like that
  or PCSX2's global auto-enable settings will not pick them up. Custom group
  names are fine but require ticking per game in Game Properties → Patches.
- Don't reproduce a group that PCSX2 already bundles in `resources/patches.zip`
  for the same serial+CRC unless you mean to shadow it; PCSX2 merges the
  bundled and loose entries and de-duplicates by group name.
- Line endings: `.gitattributes` marks `*.pnach` and `*.md` as `text`, so the
  repository stores LF and git converts on checkout (this desktop checks out
  CRLF via `core.autocrlf`). Never convert by hand. A diff that touches every
  line is a line-ending accident; `git ls-files --eol` shows which side moved.
- `author=heavyjam`. A `description=` follows the shipped ones: what the patch
  does, what it costs, for a `[60 FPS]` group whether game speed changes and
  how that was measured, any PCSX2 setting it needs (EE Overclock, a GameDB
  hardware fix to switch off, 4:3), "Tick this or X, not both" when two groups
  exclude each other, and, when any line is `place=0`, "Applied at boot, so
  restart the game after ticking it."
- Commit subjects read `Add <Group> for <Game> (SERIAL)` for a new group and
  `<Game>: <what was found>` for survey and measurement work.
- Work lands on `main` directly: no feature branches, no pull requests. From a
  harness worktree, fast-forward the primary checkout and push from there.
- `.codex/hooks.json` contains no project lifecycle hooks. Session startup
  does not automatically pull this clone. See `docs/codex-setup.md` for the
  optional manual update helper.

## Before writing a group

- Take the serial and ELF CRC from the disc that will be played, never from a
  title guess: PCSX2 shows both in Properties → Summary. A guessed serial once
  cost an hour disassembling a game the bundle had already solved.
- Audio-only undubs usually keep the retail ELF and its CRC; fan translations
  always change it. Hash the ELF before filing a CRC as uncovered.
- See what PCSX2 already ships for that serial+CRC. `patches.zip` is flat, one
  `SERIAL_CRC.pnach` entry per file; a `KeyError` means no bundled file at all:

  ```
  python -c "import zipfile;print(zipfile.ZipFile(r'<PCSX2 install>/resources/patches.zip').read('SERIAL_CRC.pnach').decode())"
  ```

## Records, devlogs and the survey docs

- `docs/deinterlace/no-interlacing-candidates.md` is the work queue: tiers, the
  NTSC-U shortlist, and a measured paragraph for every game looked at.
  `docs/deinterlace/vsrecommended-ps2-crossref.md` and
  `docs/60fps/frame-rate-survey.md` are its companions. The TSVs under
  `docs/deinterlace/data/` come from
  `python tools/scan_deinterlace_coverage.py --pcsx2 <PCSX2 install> --out docs/deinterlace/data`
  (stdlib only; the full coverage table is gitignored and rebuilt locally).
- Every investigation leaves a record, negative ones included. A game measured
  and found to need nothing gets a bold-lead paragraph in the candidates doc
  and a row in the frame-rate survey; a bundled group worth explaining gets a
  `docs/<category>/devlog-...` titled `Note:` with no patch file
  (`docs/60fps/devlog-SLUS-21006-gits-sac-60fps.md` is the model).
- A devlog opens like the existing ones: `# Devlog: <Group> for <Game>
  (SERIAL)`, a paragraph linking the pnach and any sibling devlog, then a
  `Target:` line with developer and year, the exact build (retail, undub,
  translation), boot ELF name and CRC, what PCSX2 bundles for that serial+CRC,
  and the PCSX2 version tested. A sibling devlog for the same disc may link to
  the primary's `Target:` line instead of repeating it, as the deblur devlogs
  do. Emulator and harness lessons go under
  `## Notes for next time` or `## Harness notes`, and what was considered and
  rejected under `## Deliberately left alone`, so they can be grepped across
  devlogs.

## Testing in PCSX2

- PCSX2 reads only loose files from its `patches` folder. Copy the pnach there,
  tick custom groups in Game Properties → Patches or in
  `gamesettings/SERIAL_CRC.ini` (`[Patches]`, then one `Enable = <Group>` line
  each), and restart the game. Machine-specific paths belong in
  `Codex.local.md` (gitignored), not here.
- A savestate (`.p2s`) is a zip; `eeMemory.bin` inside is the flat 32 MB EE RAM,
  the cheapest way to confirm a patched word landed and to read display envs.
- Frame rate and game speed are measured from two savestates:
  `python tools/diff_savestates.py FIRST.p2s SECOND.p2s --seconds <gap>`
  histograms the per-word EE RAM deltas, and `docs/60fps/frame-rate-survey.md`
  says how to read it. Unlike the scan script it needs numpy, and because
  PCSX2 2.x zstd-compresses `.p2s` members it also needs Python 3.14+, the
  `pyzstd` package, or 7-Zip on PATH.
- PINE (`EnablePINE = true`, TCP 28011) can write memory live, but writing a
  code word that a `place=1` line also targets, or one inside a live interrupt
  handler, crashes PCSX2. A/B code through a pnach and a restart; write only
  data over PINE.
