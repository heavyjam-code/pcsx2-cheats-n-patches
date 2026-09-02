# Devlog: 60 FPS for The Sword of Etheria (SLES-53768)

Record of how the `[60 FPS]` group in
[`patches/SLES-53768_88E95888.pnach`](../../patches/SLES-53768_88E95888.pnach) was made.

Target: Konami (KCET, 2005), PAL retail as the "UNDUB v1.0" build, boot ELF `SLES_537.68`
(6,457,864 bytes), ELF CRC **`88E95888`** - the same CRC PCSX2's bundled `patches.zip` carries
for this release, so the undub did not touch the ELF. Compiler string
`MW MIPS C Compiler (2.4.1.01)`. The game asks for NTSC (60Hz) or PAL (50Hz) at boot; the
user wanted 60, so the work below is in NTSC mode unless it says otherwise.

PCSX2 2.8.1 already bundles a `[50/60 FPS]` group for this serial+CRC (asasega):
`patch=1,EE,00511F14,word,24020001`. It works on PCSX2 and its mechanism is the same one this
patch uses, but it relies on a quirk of PCSX2's GS emulation to do so - see
[the bundled patch](#the-bundled-patch-and-why-this-one-differs). This file ships a different
group name, so the two coexist in the Patches tab.

The whole patch is one word. The work was in finding out what the game actually does with its
frames, and in proving that presenting twice as many of them does not make it run twice as fast.

## Where the 30 comes from

Nothing in this engine counts to two. There is no frame divider in the main loop, no
vsync-count parameter in use (the GS driver has one, at `0x00A20644`, and nothing in the ELF or
in the `OL.BIN` overlays ever sets it - it stays 0, which means "flip whenever a frame is
ready"). The title screen, the front-end menus and the in-engine dialogue cutscenes all
present at 60 frames per second in the shipped game, measured live.

The 30 in missions comes from a **field-parity gate**: a VBLANK_START interrupt handler that
hides the driver's "flip requested" flag on even fields, so the actual buffer swap can only
happen on odd fields - every second vblank.

The GS driver (a Konami packet scheduler, `0x006E4000`-`0x006F3000`) keeps its state in
`$gp`-relative bytes (`$gp = 0x00A28070`):

| Address | What it is |
|---|---|
| `0x00A2863F` (`gp+0x5cf`) | flip pending. Set to 1 by the display-list command `0x40`/`0x41` at `0x006E44E4`/`0x006E44FC` when a frame's packets are done; cleared by the flip handler |
| `0x006E45D8` | the driver's VBLANK_START handler: if flip pending, write DISPFB/DISPLAY for the finished buffer (`0x006E46B4`-`0x006E4728`), clear the flag, `gp+0x641 = 1` |
| `0x00A20644` (`gp-0x7a2c`) | the driver's vsync-interval setting, compared against `gp+0x641` at `0x006E45FC`. Initialised to 0; its setter at `0x006E6938` has no caller in the ELF or in any overlay |
| `0x00511F10` | the **parity gate**, a second VBLANK_START handler: `if (((GS_CSR >> 13) & 3) == 2) { saved = pending; pending = 0; flag = 1; }` |
| `0x00511EE0` | its partner, also on VBLANK_START: `if (flag) { pending = saved; flag = 0; }` |
| `0x00511DB0` | installs both (`AddIntcHandler(2, ...)`), called from the mission state machine at `0x005F4928`, two event-scene paths at `0x0060C624` and `0x0060EBD4`, and a scene initialiser at `0x00800B50` |
| `0x00511CF0` | removes them; 11 call sites, one per scene exit |

`(CSR >> 13) & 3` is CSR bit 13 (FIELD) in bit 0 and CSR bit 14 (the low FIFO status bit) in
bit 1. On PCSX2 the FIFO status is always "empty", bit 14 is always set, and the expression is
2 on even fields and 3 on odd ones. The pair is installed after the driver's handler, and the
measured behaviour says the kernel runs them first: on an even field the gate hides the flag
before the driver's handler looks at it, and on the following odd field the partner restores
it just before the driver flips. Net effect: one swap per two vblanks, always on the same
parity. In gameplay, live:

```
flips/s = 30.0    dt@0xA27D50 = 0.0330 s    parity handlers installed (ids 0x19, 0x1a)
```

and at the title screen, where nothing has installed the gate, 60.0 flips/s with the same
driver and the same divider setting of 0.

## Why the game does not speed up

This is the part that decides whether a frame-rate patch is one word or a project, and here
the engine answers it itself. The main loop at `0x00512674` starts every frame like this:

```
0051269c  jal  0x51fcf0            ; read the EE timer-0 clock (ms; 64-bit tick accumulator at 0xA42530)
005126a8  lw   v1, prev            ; 0xA27D78
005126ac  subu v1, v0, v1          ; elapsed ms since the previous frame
005126e4  lui  v0, 0x3a83 / ori 0x126f   ; 0.001f
005126f4  mul.s f20, f0, f1        ; dt = elapsed * 0.001  (seconds)
005126f8  lui  v0, 0x3d23 / ori 0xd70a   ; 0.04f
00512708  c.ole.s f20, f0          ; dt = min(dt, 0.04)
00512720  swc1 f20, -0x320(gp)     ; 0xA27D50 = dt
```

`dt` is then handed as `$f12` to every update call in the loop - the two scene objects at
`0x00512780`, the game-object update at `0x005129A4`, the three vtable calls at `0x005129D4`,
`0x005129F4` and `0x00512A14` - and read directly by another 55 sites. It is a genuine variable
timestep, clamped at 1/25 s, computed from a hardware timer (T0 at BUSCLK/16, mode `0x281`,
with the overflow interrupt at `0x0051FC50` extending it to 64 bits). At 30 fps it reads
0.0330; at 60 it reads 0.0170; the engine integrates the same seconds either way.

The one frame-counted structure found is the callback list at `0x00A32098`, serviced once
per frame by `0x00511F60`, which decrements a countdown and fires a sound-stop callback at
zero. Its only producer (`0x005120EC`) queues a countdown of 5 - a 5-frame delay before a
voice stream is released, which becomes 83 ms instead of 167 ms. Nothing else was found that
counts frames.

## The measurement

All runs are PCSX2 2.8.1, emulator at 100% (the vblank counter at `0x00A27D8C`, incremented by
a third VBLANK_START handler at `0x00511EC0`, ticks 60.0/s in every run), 2x internal
resolution, from one savestate of the first mission (the combo tutorial fight, popup
dismissed). The patched runs are a separate PCSX2 launch with the group enabled, loading the
same stock savestate; `place=1` re-applies the word on every vsync so the state comes up
patched, confirmed by reading it back.

Frame rate, counted as rising edges of the flip-pending flag and as changes of the field
select byte at `0x00A28640`, 2-3 s samples over PINE:

| Scene | stock | patched |
|---|---|---|
| title screen | 60.0 | - |
| in-engine cutscene | 60.0 | - |
| mission (tutorial fight) | 30.0 | 60.0 |
| `dt` read back from `0x00A27D50` | 0.0330 | 0.0170 |

Game speed, measured as displacement rather than pixels because the AI and camera diverge
chaotically between runs (a stock-vs-stock screenshot pair already differs in 18.5% of
pixels): from the same state, hold the left stick up for 3.00 s of wall clock, then save a
state; also save states after 3 s of no input. Diffing EE memory against the base state gives
every float that moved in both stock walks and stayed still in both idle runs - 6118 of them,
world transforms and camera included. Ratio of the patched run's displacement to the stock
run's, per field:

| Pair | median | IQR |
|---|---|---|
| stock walk 2 / stock walk 1 (control) | 1.000 | 0.998 - 1.008 |
| patched walk / stock walk 1 | 1.000 | 0.997 - 1.006 |
| patched walk / stock walk 2 | 1.000 | - |

The same diff, normalised per vblank, sorts every value that grew in all five runs: 6336
floats advance at the same per-vblank rate patched and stock (wall-clock timers - a scripted
3.5 s countdown at `0x00965BE4` reads +3.500 in every run), and the only integers that double
are the display driver's own frame counters (`0x00A206F4` and the libpad copies: 0.500 per
vblank stock, 0.999 patched). No per-entity timer doubled.

## The bundled patch, and why this one differs

asasega's `[50/60 FPS]` changes the `2` at `0x00511F14` to `1`, so the gate compares
`(CSR >> 13) & 3` against 1. On PCSX2 that value is never 1 (bit 14 is always set), so the
gate never fires and the effect is identical to this patch. On hardware the FIFO status bits
change, and the compare could match at moments the author did not intend. This patch turns
the conditional branch at `0x00511F2C` into an unconditional one:

```
00511f2c  14620006  bne v1, v0, 0x511f48   ->   10000006  b 0x511f48
```

so the hide is skipped whatever the CSR says, and both handlers stay installed and inert
(the partner at `0x00511EE0` only acts when the gate has set its flag). The cleanest
alternative, not installing the gate at all, would mean patching four call sites for the same
result.

Rejected: nopping the `sb zero` at `0x00511F44` (the flag would be saved as 1 and restored
after the driver had already flipped, producing a second, spurious swap on the next field),
and forcing the divider at `0x00A20644` (it is already 0).

## PAL (50Hz) mode and movies

The gate does not care which video mode it is gating, so the patch also lifts the 50Hz mode.
Checked in a separate patched boot with PAL selected at the prompt, in the same tutorial
mission: 50.0 flips/s, `dt` = 0.0200, field-render flag `gp+0x5cc` = 0. That flag is set
while the boot prompt is up in PAL mode and clear once the game proper starts in either mode,
so missions never use the driver's half-pixel field alternation and there is no field order
for the patch to break.

The attract-mode movie that plays when the title screen is left alone was measured in the
same PAL boot with the patch active: 49.7 and 49.3 flips/s in two 3 s samples, image intact,
no hang, and the gate's installed flag at `0x00A27D90` read 0 throughout - the title's movie
path never installs the gate, so the patch does not touch it. The fourth installer at
`0x00800B50` sits in a scene initialiser reached only through a function pointer; it was not
exercised, and if a story movie uses it the effect is the same as in missions: the swap
happens on whichever field the decoded frame lands, instead of waiting for an odd one.

## The patch

| Patch | Purpose |
|---|---|
| `00511F2C: 14620006 -> 10000006` | the field-parity vblank handler skips hiding the flip request, so the GS driver swaps buffers on every vblank instead of every second one |

`place=1`; the word is in the resident `main` segment and the handler is only installed in
missions, cutscenes and movies, so the vsync-time write is always in place before it matters,
and it also covers a stock savestate loaded into a patched session.

## Notes for next time

- PINE-writing an instruction inside a live interrupt handler crashed PCSX2 2.8.1 with
  `[EE] Impossible block clearing failure` on the second write (the first took, and measured
  60 fps). A pnach line and a restart is the safe way to A/B code that runs from an interrupt.
- PCSX2's PINE server serves one socket at a time: a second connection opened while the first
  is still alive times out on every request. Close before reconnecting, and send `LoadState`
  fire-and-forget - its reply can take longer than the load.
- The vblank counter at `0x00A27D8C` has no reader anywhere in the image. It exists, it ticks,
  and the game keeps time from T0 instead. It made a good emulator-speed check.
