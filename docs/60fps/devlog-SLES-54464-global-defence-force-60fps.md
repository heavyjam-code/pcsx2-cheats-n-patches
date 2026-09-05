# Devlog: 60 FPS for Global Defence Force (SLES-54464)

Record of how the `[60 FPS]` and `[NTSC Mode]` groups in
[`patches/SLES-54464_DD35AC9F.pnach`](../../patches/SLES-54464_DD35AC9F.pnach) were made.

Target: Sandlot / D3 Publisher of Europe (2007), the PAL release of Earth Defense Force 2, as a
raw CD image (`.bin` + `.cue`, MODE2/2352). PCSX2 2.8.1 refuses the `.cue` ("Unable to identify
the ISO image type") but opens the `.bin` directly. Boot ELF `SLES_544.64` (1,547,056 bytes),
ELF CRC **`DD35AC9F`** - the same CRC PCSX2's bundled `patches.zip` carries for its
`[Widescreen 16:9]` file, the only group it ships for this serial. Compiler string
`MW MIPS C Compiler (2.4.1.01)`, `$gp = 0x00281770`. No symbols; the engine keeps its C++ class
names as strings (`clGiantAnt`, `clPlayerObject_Male`, `clVgsControl`, `utKksSystem`), which is
how the engine core was told apart from the game.

The blur on distant objects is two separate passes, a depth of field and an additive haze,
and has [its own devlog](../deblur/devlog-SLES-54464-global-defence-force-remove-blur.md); the
`[Remove Blur]` group in the same file comes from there. The progressive switch is
[the No-Interlacing devlog](../deinterlace/devlog-SLES-54464-global-defence-force-no-interlacing.md).

The request was 60 fps, or 50 if the PAL disc could not do 60. The disc turned out to be a
stranger thing than either: a game whose logic already runs at 60 Hz, on a 50 Hz display, at a
frame rate that is decided by how long the EE takes rather than by anything the game counts.
The patch is five words, and four of them are the video mode.

## What the PAL disc actually does

Display setup is one call, `sceGsResetGraph(0, 1, 3, 0)` at `0x0012C038`: full reset, interlaced,
**PAL**, field mode. The frame buffers are 640x448 (`0x0012AEE8`/`0x0012AEF8` in the display
initialiser), and the builder at `0x0012ADD0` fills a per-buffer table at `0x0027B2F0` with the
privileged register values that the flip routine `0x0012BD70` later copies into `PMODE`,
`DISPFB1/2` and `DISPLAY1/2`:

```
0012B0C8  daddiu v0, zero, 0x290     ; DISPLAY.DX = 656
0012B07C  lui    at, 6
0012B0B4  ori    v0, at, 0x8000      ; DISPLAY.DY = 0x68 = 104: the 448 lines centred on PAL's 512
0012AFE0  lui    at, 0x1b
0012B074  ori    v0, at, 0xf000      ; DISPLAY.DH = 0x1bf = 447
0012B08C  daddiu v0, zero, 0x9ff     ; DISPLAY.DW = 2559
0012B0A0  lui    v0, 0x180           ; MAGH = 3
```

The frame clock is not the vblank. It is EE Timer 1: the timer initialiser `0x0013E370` (called
from a static constructor at `0x002691A4`) installs handler `0x0013E500` on INTC cause 10, mode
`0x5C2` (BUSCLK/256 = 576 kHz, zero-return, compare interrupt) and compare `0x2D00` = 11520
-> **50 Hz**. Then the display initialiser `0x0012A5B0`, called from the game's init at
`0x001102B8`, ends with `0x0013E560(timer, 0x2580)` at `0x0012A9AC` - compare 9600 -> **60 Hz**,
and nothing sets it again. Read live over PINE the compare at `0x0027B798` is `0x2580` and the tick
counter `0x0027B038` advances 60.0 times a second. D3P's port put a 50 Hz constant in the timer
init and the NTSC display init overrode it; the shipped PAL game runs the NTSC clock on a 50 Hz
screen.

The timer handler's callback `0x0012CD90` increments `0x0027B034` (ticks since the last present)
and `0x0027B038` (ticks since boot). The present function `0x0012D200(mode)` waits for the GS to
finish the previous frame (`0x0012D140` spins on the busy flag `0x0027B678`), then if `mode` is 1
spins until `0x0027B034` changes - the next tick edge - copies it to `0x0027B030` ("ticks the last
frame took"), zeroes it, bumps the presented-frame counter `0x0027B03C`, and flips. `sceGsSyncV`
(`0x001592D0`) has five callers and none of them is in the frame loop: the display init, a wait
helper at `0x0013926C`, and the movie player's field loops at `0x0013CFE0`/`0x0013D15C`. The flip
is asynchronous to the vblank, in either video mode.

## The main loop

`0x00110950`, called once from `main` at `0x001BBCB4`, runs until the exit byte `0x00279C80` is
set. Per iteration:

```
001109A8  jal  0x12ad80             ; s3 = ticks the previous frame took (0x0027B030)
001109B4  sltiu at, s3, 3
001109B8  beqz at, 0x110a08         ; 3 ticks or more: present(0), s4 = 16
001109C0  beqz s4, 0x110a18         ; s4 == 0: present(1)  - wait for the next tick
001109C8  jal  present(0); s4--     ; s4 >  0: present(0)  - no wait
...
00110A28  sltiu at, s3, 5
00110A34  addiu s3, zero, 4         ; cap the step count at 4
00110A48  beqz s3, draw
00110A58  ... pad read, 0x00113DD0 (task update), sound, counters ...   ; one logic step
00110C18  addiu s1, s1, 1
00110C1C  sltu v0, s1, s3
00110C20  bnez v0, 0x110a58         ; repeat s3 times
00110C28  ... 0x00113DE0 (task draw), 0x00111E20, packet build ...     ; draw once
00110E40  beqz exit, 0x1109a8
```

So the world advances one logic step per 60 Hz tick whatever the frame rate is: a frame that
took two ticks is followed by two steps and one draw. There is no reader of a clock anywhere in
the game side of the image - the only `mfc0 Count` users are the display module's profiling
stores, and no code reads `T1_COUNT` - so this catch-up is the whole timing model.

Two consequences:

- **The frame rate is `ceil(EE work / tick)`.** In stock PCSX2 at 100% EE the title screen presents
  49.7 frames a second (frames of one tick with a few of two), missions present exactly 30
  (every frame two ticks). EE Overclock 300% turned mission 1 into a locked 60 with no other change,
  and the game did not speed up: from one savestate, a 3-second walk under 300% ended at the same
  spot, in the same hit animation, with the same 185 HP and the same radar, as the stock 30 fps
  walk. The savestate-diff method was tried first and gave nothing usable here because the
  interesting differences are event timings, not displacements; two end frames were the honest
  instrument again.
- **30 fps is sticky.** Once a frame needs two ticks, the next frame runs two steps plus a draw,
  which is heavier than the one step plus a draw that has to fit in a tick for the game to climb
  back. On the street of the second test position, stock 100% EE ran at 60 fps in one load of the
  savestate and at 30 in another, and stayed wherever it landed; 130% EE, which shrinks the
  two-step frame under a tick, held 60 there every time. The engine's own answer to slow frames
  exists but only wakes at three ticks: `present(0)` and sixteen frames without waiting.

## The patch

| Patch | Purpose |
|---|---|
| `0012C034: 24060003 -> 24060002` | `sceGsResetGraph` omode 3 (PAL) -> 2 (NTSC): 60 Hz output |
| `0012B07C: 3C010006 -> 3C010003`, `0012B0B4: 34228000 -> 34222000` | `DISPLAY.DY` 104 -> 50, the NTSC top margin for a 448-line picture |
| `0012B0C8: 64020290 -> 64020280` | `DISPLAY.DX` 656 -> 640: the PAL value was the SCE default plus 4, this is the NTSC default plus 4 |
| `001109B4: 2E610003 -> 2E610002` | `[60 FPS]` only: the no-wait catch-up starts at 2-tick frames instead of 3 |

The display words run once at boot, so they are `place=0`. The loop word is plain code in the
resident main loop and is `place=1`, so a savestate from a stock boot loaded into a patched
session still gets the new loop (the video mode it does not get back; PCSX2 savestates carry the
GS registers, so states saved under PAL come back PAL until the next boot).

The libgraph `sceGsSetDefDispEnv` used by the movie player reads the mode from `sceGsGParam`
(`0x0024B090`) and follows the switch on its own. `DH` stays 447 and the buffers stay 640x448, so
nothing about the picture changes except the refresh.

With the threshold at 2, a 2-tick frame is presented as soon as it is ready and the sixteen
frames after it do not wait either. In a scene that fits a tick that is a burst of a few frames -
some of them redraws of the same world state, since a frame that sees no tick edge runs no step -
and then the loop is back to waiting for tick edges at a clean 60. In a scene that does not fit,
the loop stays uncapped: 36-42 presents a second on the bridge at mission start against the
stock 30, with a mix of one- and two-step frames, which is uneven and is why `[NTSC Mode]` exists
for anyone who would rather have the stock lock. It is the engine's own 20 fps behaviour
extended upward, not new code.

Measured, all PCSX2 2.8.1 at 2x internal resolution, 3-second samples over PINE of the tick
counter `0x0027B038`, the presented-frame counter `0x0027B03C` and a histogram of the
ticks-per-frame word `0x0027B030`:

| Build | EE | Scene | ticks/s | presents/s | ticks per frame |
|---|---|---|---|---|---|
| stock | 100% | title menu | 60.0 | 49.7 | 1, some 2 |
| stock | 100% | mission 1, carried by an ant | 60.0 | 30.0 | all 2 |
| stock | 100% | mission 1 start (bridge) | 60.0 | 30.0 | all 2 |
| stock | 100% | street position, two loads | 60.0 | 30.0 / 60.0 | all 2 / all 1 |
| stock | 130% | street position | 60.0 | 60.0 | all 1 |
| stock | 180% | street position | 60.0 | 60.0 | all 1 |
| stock | 300% | street position | 60.0 | 60.0 | all 1 |
| loop word only (PINE) | 100% | bridge | 60.0 | 35.7 / 37.3 / 42.3 | 2 and 1 mixed |
| `[60 FPS]` | 100% | title menu | 60.0 | 52.7 | 1, some 0 |
| `[60 FPS]` | 100% | mission 1 start (bridge) | 60.0 | 33-34 | 79% 2, 21% 1 |
| `[60 FPS]` | 180% | mission 1 start (bridge) | 60.0 | 60.0 | all 1 |

The patched boot logs `UpdateVSyncRate: Mode Changed to NTSC`, `sceGsGParam.omode` reads 2, and
the `DISPLAY1` value in the table reads `0x001BF9FF_01832280`: DW 2559, DH 447, MAGH 3, DY 50,
DX 640. Two 3-second walks from the street savestate in the same session, one with the loop word
and one without, produced the same end frame (same spot, 200 HP, same radar), so the redraw
frames and the uncapped presents change nothing the game simulates.

## Movies and the rest

`D3LOGO.PSS` is 640x480 at 30 fps and `OPMOVIE.PSS` is 720x480 at 29.97 fps - NTSC sources that
the PAL disc played on a 50 Hz raster. The movie player builds its own 720x512 display
environment (`sceGsSetDefDispEnv` at `0x0013CF9C`, centring the video in it at `0x0013D074`); in
NTSC mode a 512-line environment hangs 32 lines into overscan on a television, which costs the
video's lower 16 lines of black border and nothing of the picture, and PCSX2 shows all of it.
Left alone.

The timer runs at exactly 60.000 Hz off the bus clock and NTSC vsync is 59.94, so once every
seventeen seconds or so one presented frame is shown twice. In PAL mode the same free-running
clock met a 50 Hz raster and every fifth frame was held for an extra field; that judder is what
the NTSC words remove, for 30 fps content as much as 60.

Not done: a real `[50 FPS]`. The timer initialiser's own `0x2D00` would give a 50 Hz clock and a
frame per field on the PAL raster with no beat at all, but it also makes the world advance 50
steps a second instead of 60 - a game 17% slower than the disc as shipped, which already plays at
NTSC speed. With 60 possible, that trade was not worth a group.

## Notes for next time

- PCSX2 opens a MODE2/2352 `.bin` directly; its `.cue` parser did not take this one. A plain
  2048-byte ISO converted from the bin also lists fine in 7-Zip for pulling the ELF.
- PINE reads of hardware registers (`0x10000800` `T1_COUNT`, `T1_COMP`) return 0; it does not
  route through the hardware handlers. Read the game's own copy of a timer setting instead.
- A tick-driven catch-up loop shows up as "ticks-last-frame has one reader" and a step loop that
  runs that many times; the savestate float diff reads 1.0 for everything and screenshots agree,
  which is the correct answer, not a failed measurement.
- Savestates saved with the in-game pause menu open come back in the light 1-tick regime; states
  saved in play come back in whichever regime they were in. That is the hysteresis showing, and it
  makes "stock ran 60 here once" a real observation rather than noise.
- The soldier gets bitten if the ants are close; a walk test needs a quiet street and a state saved
  after `Retry Stage`, and a wall in front of the soldier caps the displacement after a second.
