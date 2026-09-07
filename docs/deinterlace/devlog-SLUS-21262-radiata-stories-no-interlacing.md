# Devlog: No-Interlacing (480p) for Radiata Stories (SLUS-21262)

Record of how the `[No-Interlacing]` group in
[`patches/SLUS-21262_47B9B2FD.pnach`](../../patches/SLUS-21262_47B9B2FD.pnach) was made. The
frame-rate side of this disc is unfinished and written up separately in
[the frame-rate survey](../60fps/frame-rate-survey.md); the paragraph this devlog replaces is in
[the candidates doc](no-interlacing-candidates.md#corrections-and-shaky-claims).

Target: tri-Ace / Square Enix (2005), NTSC-U, the undub disc. `SYSTEM.CNF` reads
`BOOT2 = cdrom0:\SLUS_212.62;1`, `VMODE = NTSC`; boot ELF `SLUS_212.62`, 518,576 bytes, ELF CRC
**`47B9B2FD`** (XOR of every little-endian u32 of the file). PCSX2 2.8.1 bundles **no pnach for
this serial at any CRC** - `resources/patches.zip` has 4704 entries and not one of them is
`SLUS-21262_*`. `$gp = 0x001862F0`. Tested on PCSX2 2.8.1. The disc here is the undub; whether the
retail ELF hashes to the same CRC was not checked, so treat the file name as covering this build
only.

One line. The game ships a working progressive mode and tells the player about it on screen, so
there was nothing to reverse-engineer and nothing to deinterlace - only a flag to hold down. The
interesting part is that the obvious lever, the branch, is the wrong one.

## The game says it itself

Radiata's Screen options page prints:

> If you have a progressive scan television, press the Triangle button and the Cross button at the
> same time to switch to progressive scan mode.

So the row for this game in [`data/fieldrender-gaps.tsv`](data/fieldrender-gaps.tsv) -
`640x448 -> 1280x447`, which grades as TIER-A - is a measurement of the interlaced default, not a
statement that the engine renders one field at a time. The 480p list is the one that is right. This
is a **TIER-C** job: a real progressive path exists and simply is not selected.

## The mode selector

The flag is a byte at **`0x0019E9C4`**, and the ELF's single loadable segment is
`VA 0x00100000, filesz 0x7E300, memsz 0xA2380` - so the loaded image ends at `0x0017E300` and
`0x0019E9C4` is **`.bss`**. That matters for `place=`, below.

The read is inside `main` (`0x00124630`, called from the crt0 stub at `0x00100208`), about `0x450`
bytes in:

```
00124A74: 3c01001a  lui   at, 0x1a
00124A78: 9022e9c4  lbu   v0, -0x163c(at)      ; the flag, 0x0019E9C4
00124A7C: 10400008  beq   v0, zero, 00124AA0   ; clear -> interlaced arm

00124A80: 0000202d  daddu a0, zero, zero       ; progressive arm
00124A84: 0000282d  daddu a1, zero, zero       ;   inter  = 0
00124A88: 24060050  addiu a2, zero, 0x50       ;   omode  = SCE_GS_DTV480P
00124A8C: 0c044202  jal   00110808             ;   sceGsResetGraph
00124A90: 24070001  addiu a3, zero, 1          ;   ffmd   = 1

00124AA0: 24050001  addiu a1, zero, 1          ; interlaced arm: inter = 1
00124AA4: 0000202d  daddu a0, zero, zero
00124AA8: 24060002  addiu a2, zero, 2          ;   omode  = SCE_GS_NTSC
00124AAC: 0c044202  jal   00110808
00124AB0: 00a0382d  daddu a3, a1, zero         ;   ffmd   = 1
```

`0x00110808` is `sceGsResetGraph`: it resets the GS through an `sd` of `0x200` to `0x12001000`
(`CSR`) before programming the mode. So the two arms are `sceGsResetGraph(0, 0, 0x50, 1)` and
`sceGsResetGraph(0, 1, 2, 1)`, and the only thing standing between them is one byte in `.bss`.

## Two ways to force it, and only one is correct

- **NOP the branch** - `00124A7C: 10400008 -> 00000000` - so the progressive arm always runs.
  PCSX2 duly logs `Mode Changed to SDTV 480p` and then renders a **half-height picture**,
  `1280x448` at 2x where stock is `1280x896`. Forcing the `sceGsResetGraph` call skips whatever
  else the real path does to the buffers. Wrong lever.
- **Set the flag** - `patch=1,EE,0019E9C4,byte,00000001`. Same `SDTV 480p`, and the render is the
  full `1280x896`, pixel-for-pixel the stock picture with the interlace gone. One line, and it is
  the game's own code doing the work.

That is the general lesson worth carrying: when a game exposes a progressive mode as a *setting*,
drive the setting. The branch is downstream of everything else the selection does.

## Who else touches the flag

A whole-image scan resolving `lui`/`addiu` bases - never displacements alone, see
[the Cowboy Bebop devlog](devlog-SLPS-25550-cowboy-bebop-no-interlacing.md) - finds exactly **one
absolute accessor** of `0x0019E9C4`: the `lbu` at `00124A78`. That is not the whole story, and an
earlier note in the candidates doc that read it as "the menu handler must live in an overlay" was
half right for the wrong reason. Two more sites reach the same byte through an object pointer:

```
00124150: 27bdfff0  addiu sp, sp, -16          ; set_progressive(obj, flag)
00124154: 3c010001  lui   at, 0x1
0012415C: 00810821  addu  at, a0, at
00124160: 10a00009  beq   a1, zero, 00124188
00124164: a0251484  sb    a1, 0x1484(at)       ; obj + 0x11484
                                               ; ... then the same two arms as above
001244F8: a0201484  sb    zero, 0x1484(at)     ; obj + 0x11484, in the video object's reset
```

The object is `0x0018D540` (`lui a0,0x19 ; addiu a0,a0,-10944`, materialised at `00124AB8` and at
four other call sites), and `0x0018D540 + 0x11484 = 0x0019E9C4`. So `00124150` is
`set_progressive(obj, flag)`: it stores the byte **and** calls `sceGsResetGraph` with the matching
arguments, which is exactly what a Triangle+Cross handler would do. It has **no `jal` caller in the
boot ELF**, so the handler that calls it is in an overlay - the original conclusion survives, it
just was not reached from "one accessor".

## Why `place=1`

Three reasons, and they are the same three that make a `place=0` line wrong here:

1. `0x0019E9C4` is in `.bss`, so the runtime's clear would zero a `place=0` write after it lands.
2. `001244F8` clears it again in the video object's own reset.
3. `00124150` clears it whenever the in-game toggle is used.

A `place=1` line is re-applied every vsync and beats all three. The cost is the third one: while
the group is ticked, the Screen page can set the flag to 0 but it is back to 1 before the next
frame, so the in-game toggle only works in one direction. The `description=` says so.

## What is verified, and what is not

Verified live: `Mode Changed to SDTV 480p` from the first frame, full `1280x896` at 2x, holding
through the settings screens and into the opening cinematic.

**Not verified: 3D gameplay.** This is the one thing left before the group is called done, and it
is not a formality - Dragon Quest VIII rendered happily on its settings screen under the same class
of patch and then went black the moment it left it
([that devlog](devlog-SLUS-21207-dragon-quest-viii-no-interlacing.md) is the whole story of finding
out why). The failure mode to watch for is a black screen or a half-height picture after leaving
the front end.

## Harness notes

- **Radiata cannot be driven past its first-boot Screen menu with `PostMessage` key input**, and
  its Triangle+Cross progressive toggle does not register that way either, however long the two
  key-downs are held. Both need a human on the pad. That is why the gameplay check above is still
  open, not because it is hard to look at.
- The usual rule applies with more force than usual here: **A/B a display-mode patch boot-to-boot,
  never by hot-toggling from a savestate.** PCSX2 does not fully re-derive its GS display state
  when `SMODE2` changes mid-session, and the vertically-magnified frames it produces will make a
  comb-energy metric report a clean 2:1 improvement that does not exist.

## Deliberately left alone

- **The branch at `00124A7C`.** Measured, half-height, documented above. Nothing here needs it.
- **The flag write in `00124150`.** Patching the setter instead would preserve the in-game toggle's
  "off" direction, but it is one more instruction to hold and the flag line already works; the
  toggle is a convenience the description accounts for.
- **Frame rate.** 30 fps is confirmed - over a 10.12 s gap, 14 heap counters at 29.9/s against 4
  system counters at 59.9/s - and the lever was not found. Progress notes for whoever picks it up
  are in [the frame-rate survey](../60fps/frame-rate-survey.md). No `[60 FPS]` group ships for this
  disc.
