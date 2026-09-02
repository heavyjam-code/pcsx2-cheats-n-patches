# Devlog: No-Interlacing for Ghost in the Shell: Stand Alone Complex (SLUS-21006)

Record of how [`patches/SLUS-21006_95CC86EF.pnach`](../../patches/SLUS-21006_95CC86EF.pnach)
was made. Two words, and both of them were predicted before the game was booted:
the game already draws a full 640×448 frame, so all that stands between it and a
progressive picture is the interlace bit — plus the DISPLAY origin that has to move
with it.

Target: Bandai / Cavia (2005), the `Ghost in the Shell Stand Alone Complex (U)[UNDUB]`
ISO, boot ELF `SLUS_210.06` (3,684,156 bytes), ELF CRC **`95CC86EF`**. The undub is
audio-only: that CRC is the retail one, and `resources/patches.zip` ships a
`SLUS-21006_95CC86EF.pnach` for it, so the build is confirmed without a second dump.
Tested on PCSX2 2.8.1, Vulkan, 2× internal resolution.

## The free lead

Nothing in any region has a deinterlacing group — the only shipped files are a
one-line `[60 FPS]` for NTSC-U and a `[50/60 FPS]` + `[NTSC Mode]` pair for PAL
`SLES-53020`. But that PAL `[NTSC Mode]` group is a map of the exact code this job
needs:

```
patch=1,EE,00265804,word,24060002    // li a2, 2      -> omode = NTSC
patch=1,EE,002655A0,word,240401C0    // li a0, 0x1C0  -> 448 scanlines
```

`li a2,2` is an `omode` argument and `li a0,0x1C0` is a display height, so PeterDelta
had already found the video-mode init in the PAL build. The NTSC-U twin sits one
function further along at `0x266df4`, and finding it took one `jal` scan.

## How the game does video (map of the ELF)

EE virtual addresses; the loadable segment maps `file_offset = va - 0xff000`. Full
section headers, no `.sndata`/`SNR1` symbol table, so this was ordinary code reading.

| Address | What it is |
|---|---|
| `0x2d0084`+`0x10*n` | syscall stub table; `SetGsCrt` (#2) is the stub entered at `0x2d00a0` |
| `0x2a4548` | `sceGsResetGraph(mode, inter, omode, ffmd)` — fills GParam, tail-calls `SetGsCrt`. **Three callers** |
| `0x401800` | `sceGsGParam` |
| `0x266df4` | NTSC init: `heightSet(0x1C0)` then `sceGsResetGraph(0, 1, 2, 1)` |
| `0x266e9c` | **DTV480P init**: `heightSet(0x1E0)` then `sceGsResetGraph(0, 0, 0x50, 1)` — the boot-menu progressive mode |
| `0x266fa8` | third `sceGsResetGraph(0, 1, 2, 1)`, on the mode-restore path |
| `0x2661b4` | height setter: stores h to `gp-0x3ad8`, h/2 to `gp-0x3ad0`, plus float copies |
| `0x396960` | the display object |
| `0x1b9c44` | fills the object's CRTC config: `+0x1720` W, `+0x1724` H, `+0x1730` INT, `+0x1734` FFMD, `+0x1738` mode |
| `0x1b9c60` | fills the **draw** env: `+0x1744/48` = 640×448, `+0x174c/50` = XYOFFSET = `(2048 − W/2)<<4`, `(2048 − H/2)<<4` |
| `0x1bb078` | **the display-env builder** — reads the config at object`+0x1718`, writes the env at object`+0x1778`. Three call sites, all with that same pair |
| `0x1bb174` | the only writer of the GS CRTC registers: pushes env `+0x00`→PMODE, `+0x08`→SMODE2, `+0x18`→DISPFB1/2, `+0x20`→DISPLAY1/2 |
| `0x3984c0` / `0x3984d0` | per-mode DX and DY offset tables, `[0]`=NTSC `[1]`=PAL `[2]`=DTV480P |

The game does **not** use `sceGsSetDefDispEnv`. A scan for libgraph's `DY += 0x32`
/ `DY += 0x19` constants returns nothing anywhere in the image; Cavia wrote their own
builder. It computes the same things by different arithmetic:

```
mode = cfg[0x20]
if (mode == 2) { W *= 2; }                     // DTV480P doubles the pixel clock
else           { if (cfg[0x1c]) H *= 2; }      // FFMD=FRAME doubles a half-height buffer
env.SMODE2  = cfg[0x18] | (cfg[0x1c] << 1)     // INT | FFMD<<1
env.DISPLAY = DX | DY<<12 | MAGH<<23 | DW<<32 | DH<<44
   where DY = DYtable[mode] + cfg[0x14]
         DH = H - 2
```

The whole job is in that `SMODE2` line and that `DY` line.

## The measurement

Read out of RAM over PINE rather than guessed from screenshots, and it agreed with
the static read on every field:

```
config @0x398078 : W=640  H=448  DX=2  DY=-4  INT=1  FFMD=0  mode=0
env    @0x3980d8 : SMODE2=1          -> INT=1, FFMD=0   (interlaced, FIELD mode)
                   DISPLAY DH=447, DY=50, MAGH=4, DW=2557
draw env         : 640x448  OFX=27648  OFY=29184
```

Two numbers settle the tier. `SMODE2 = 1` is **FIELD** mode — the GS reads alternate
lines out of a full-height buffer — and `DH = 447` is the whole 448-line frame, not a
doubled half-frame. The draw env confirms it from the other side: one fixed `OFY`,
with no per-field alternation anywhere, so the game renders all 448 lines every frame.
That is TIER-B, the 1–3 instruction case, and the 2× capture duly measured
**1278×894** rather than a half-height field.

So nothing needs to be un-doubled and no half-line offset needs removing. The buffer
is already progressive; only the flag on it is wrong.

## The two words

**`0x1bb0f4`: `lw v0, 0x18(t3)` → `li v0, 2`.** This is the `INT` half of
`SMODE2 = cfg[0x18] | (cfg[0x1c] << 1)`. Forcing the base to 2 makes SMODE2 read
`INT=0, FFMD=1` — non-interlaced, read every line — which is the same value libgraph's
own non-interlace branch produces, and the same value this game's 480p path already
uses. `v0` is dead by the next instruction (`0x1bb108` reloads it with W), so nothing
else shifts.

Patching the builder rather than the config covers all three call sites at once, and
it deliberately leaves `cfg[0x1c]` alone: that flag is not just FFMD, it is also the
`H *= 2` trigger. Setting it to get FFMD=1 would have doubled `DH` to 894 and produced
exactly the "picture is twice as tall" failure it looks like it should fix.

**`0x3984d0`: `0x36` → `0x1d`.** DISPLAY.DY counts **half-lines while INT=1 and whole
scanlines once INT=0**, so the origin has to halve when the interlace bit clears.
`DY = DYtable[0] + cfg.DY = 54 − 4 = 50`; the progressive equivalent is 25, so the
table entry goes to 29. Both tables are read at exactly one instruction each
(`0x1bb0cc`, `0x1bb0e0`) and indexed by mode, so entry `[0]` reaches the NTSC
interlaced path and nothing else.

This is the trap the [Mega Man X7 job](devlog-SLUS-20487-mega-man-x7-no-interlacing.md)
recorded, arriving in a different shape: there it was `DH` and `DY` that had to move
together, here `DH` is already correct and `DY` alone is wrong. It is invisible at
PCSX2's defaults, which normalise the CRTC offset, and unmissable the moment
**Screen Offsets** is on.

## Verification

The A/B is boot-to-boot with the pnach doing the switching — including the "stock"
side, which loads a group that writes the **original** word `8d620018` back. Both runs
then load the identical savestate, so the compared frames are the same scene down to
the animation phase, and neither run depends on hot-writing code into a live session.

| Screen Offsets | stock vs patched | result |
|---|---|---|
| off (default) | `8d620018` vs `24020002` + DY | **byte-identical PNGs** |
| on (`pcrtc_offsets`) | `8d620018` vs `24020002` + DY | **byte-identical PNGs** |
| on | stock vs SMODE2 **without** the DY word | MSE 1152; aligns at **−50 px @2× = −25 lines**, black band across the top 48 rows |

That middle row is the whole argument for the patch being free: the rendered pixels do
not change at all. What changes is a flag PCSX2 reads, and PCSX2 then stops running a
deinterlacer over a frame that never needed one. The third row is the DY word earning
its place — and the −25 lines is exactly the predicted half-line/scanline factor,
measured rather than assumed.

Also checked: `SMODE2` reads back `2` live, `DISPLAY` moves from `…01832288` to
`…01819288` (DY 50 → 25) and nothing else in the register changes, the intro FMVs and
the boot sequence play normally, and gameplay is stable.

## Deliberately left alone

- **The boot-menu 480p mode** (`0x266e9c`, `omode = 0x50`). The game has a real
  progressive mode behind a menu selection at `s0+0x29b8`, and forcing it is a
  plausible separate `[480p Mode]` group. It is a different render height (640×480)
  and a different code path; the patch does not touch it, and by construction cannot:
  mode 2 takes the `W *= 2` branch, its `SMODE2` already evaluates to 2 both before
  and after, and it reads `DYtable[2]`.
- **PAL mode 1.** `omode` is 2 or 0x50 on this build; the entry is unreachable.
- **The `[60 FPS]` group.** PCSX2 already bundles a working one for this exact
  serial+CRC — see [the 60 FPS note](../60fps/devlog-SLUS-21006-gits-sac-60fps.md) for
  what it does and why it does not change game speed.

## Harness notes

- The undub ISO's ELF is byte-identical to retail, so `patches.zip` was usable as a
  CRC oracle. Worth checking before assuming a translated or undubbed disc needs its
  own file — audio-only undubs frequently do not move the ELF at all.
- **A savestate cannot be the baseline for a display-mode A/B.** The state carries the
  patched instruction *and* the built env, so loading a state saved under the patch
  reproduces the patched CRTC state even with the pnach disabled — the "unpatched"
  run silently is not one. Writing the original word back through a pnach group makes
  the savestate usable for both sides, which is what turns a scene-matched A/B into
  byte-identical PNGs.
- The env is rebuilt and re-pushed continuously, so a PINE write to `env+8` is reverted
  within a frame and reads back as whatever the builder produces. Patch the builder,
  not its output.
- PINE's metadata opcodes (`0xF2` SaveState, `0xF4` Title, `0xF5` ID, `0xF8` Status)
  all return the failure byte on this build while every memory read/write opcode works
  normally. Use the `F1`/`F3` hotkeys via `PostMessage` for save/load states.
