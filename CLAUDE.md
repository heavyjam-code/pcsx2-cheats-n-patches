# CLAUDE.md

Hand-made PCSX2 `.pnach` patches. File format reference: `docs/pnach-format.md`.
Start new patches from `templates/template.pnach`.

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
| Addresses, disassembly, why each value, what was tried and ruled out | `docs/devlog-SERIAL-<slug>.md` |

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
- Files are CRLF (`.gitattributes` marks `*.pnach` and `*.md` as text).
