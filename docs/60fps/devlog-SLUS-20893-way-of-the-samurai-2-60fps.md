# Devlog: 60 FPS for Way of the Samurai 2 (SLUS-20893)

Record of how the `[60 FPS]` group in
[`patches/SLUS-20893_158FA006.pnach`](../../patches/SLUS-20893_158FA006.pnach) was made.

Target: Acquire / Capcom (2003-2004), NTSC-U retail as the "Undub v1.1" build, boot ELF
`SLUS_208.93` (2,025,136 bytes), ELF CRC **`158FA006`** - the same CRC PCSX2's bundled
`patches.zip` carries for its `(Undub)` widescreen file, so the undub did not touch the ELF.
Compiler string `MW MIPS C Compiler (2.4.1.01)`, `$gp = 0x002F59F0`. PCSX2 bundles only a
`[Widescreen 16:9]` group for this serial+CRC; there is no 60 FPS group to shadow.

The frame cap is one word and fell out of the display code in an hour. The other two words are
the answer to "the game now runs at double speed", which is the whole story of this patch: the
engine steps its world once per presented frame, nothing measures real time, and the lever
that fixes that turned out to be the animation system's clock.

## Where the 30 comes from

The renderer keeps a display context whose pointer sits at `0x002EE670` (`gp-0x7380`); at
runtime it is a heap object at `0x0059E9F0`. Its present function `0x00131240` blocks until
enough vblanks have passed:

```
00131270  jal  0x104b38            ; wait one vsync
0013127C  lw   v1, -0x755c(gp)     ; 0x2EE494, vblank counter (the vsync handler's)
0013128C  lw   v0, 0x10(s1)        ; vblank count at the previous present
00131290  subu v1, v1, v0
0013129C  lw   v0, 0xc(s1)         ; the interval
001312A0  slt  v0, v1, v0
001312A4  bnez v0, 0x131270        ; not yet: wait another
001312C8  sw   v1, 0x14(s1)        ; how many it took
001312D4  sw   v0, 0x10(s1)
```

| Field of the context | Meaning |
|---|---|
| `+0x0c` | **vsync interval** - fields per presented frame |
| `+0x10` | vblank counter value at the last present |
| `+0x14` | fields the last frame actually took (written, never read) |

The engine already knows how to run with an interval of 1: the branch at `0x001312D8`
(`slti at, v0, 2`) only refreshes the per-field DISPLAY offset when the interval is below 2.
The field is written once, in the display initialiser `0x001315D0` (`sw s1, 0xc(s4)` at
`0x001319DC`, from its `a3`), which is called from `0x00131C60` (the value arrives in `t3`),
which is called once from the game's display setup at `0x001E1BF0`:

```
001E1C0C  addiu a2, zero, 2
001E1C28  addiu t0, zero, 0x280     ; 640
001E1C2C  addiu t1, zero, 0x1c0     ; 448
001E1C34  move  t3, a2              ; interval = 2   <- patched to  addiu t3, zero, 1
001E1C38  jal   0x131c60
```

Read live over PINE with the counters at `0x002EE494` (vblanks) and `0x002EE4A0` (presented
frames), 3 s samples:

| | vblanks/s | frames/s |
|---|---|---|
| stock, interval 2 | 60.0 | 30.0 |
| interval written to 1 | 60.0 | 60.0 |

It holds 60 on a Radeon 880M at 2x internal resolution. The word at `0x001E1C34` runs once
at boot, so the line is `place=0`.

## Why the game speeds up, and what does not

The main loop is render, present, repeat; the simulation runs once per iteration and nothing
in it reads a clock. A 3-second walk at interval 1 covered twice the street. So this is a
fixed-step engine, and the patch has to halve the step.

The engine does carry one frame-rate parameter: the word at `0x002EDA00` (`gp-0x7ff0`),
initialised to 30 in `.sdata` and never written at runtime. The PAL build has 25 there
(`0x00164200` compares it with 25 to pick the PAL display offset), and the script VM exposes
it to the game's scripts as `GetFPS` (`0x001E7F40`). It is read at some 236 sites, and they
sort into three kinds:

| Use | Count (float sites) | Example |
|---|---|---|
| `seconds * FPS` -> frames | 37 | `0x001BD8B0`: `(ms / 1000.0) * FPS` |
| `delta * 30 / FPS` per frame | 7 | `0x002B55B4`: `x -= 16 * k * (30 / FPS)` |
| frames authored at 30 `* FPS / 30` | 4 | `0x00286C00`: a random-interval scheduler |

All three keep their wall-clock meaning when the constant says 60 and the game runs 60
steps a second, which is what the second patch word does. What the constant does not reach
is movement: setting it to 60, whether live or from boot, changed nothing about the double
speed, because characters in this game move with their animations and the animation clock
does not consult it.

## The animation clock

Every character owns a motion player, a `0x170`-byte object allocated at `0x001CC8C0` and
stored at `character + 0x1B4`. Its constructor `0x001376E0` lays it out:

| Offset | Init | Meaning |
|---|---|---|
| `+0x00` | 0.0 | current frame of the playing motion (float) |
| `+0x04` | **1.0** | **frames advanced per step** |
| `+0x08` | 0.0 | copy of the frame after the step |
| `+0x24` | 0.0 | blend countdown |
| `+0x28` | 7 | flags; bit 0 = playing |
| `+0x164` | `0x002EA9C0` | vtable |

The step is vtable slot 3, `0x00137860`, reached only through `jalr`:

```
00137AC8  lwc1 f1, 4(v0)           ; speed
00137AD4  sub.s f0, f0, f1         ; blend -= speed
00137B30  lwc1 f1, 4(v0)
00137B38  lwc1 f0, 0(v0)
00137B3C  add.s f0, f0, f1         ; frame += speed
00137B44  swc1 f0, 0(v0)
```

with the loop-wrap logic (`0x00137990`-`0x00137A14`) subtracting the loop length while the
frame is past the end, so fractional frames are fine. The `NowFrame : %d` debug print at
`0x0027C0C0` and the getter `0x00143A90` read the same `+0x00`, converting to int. Nothing in
the image writes `+0x04` except the constructor: the only other stores to a `+4` in the
motion library belong to vector helpers on different objects, and no code loads
`character+0x1B4` and then stores to it. A savestate scan for the vtable word found 18 live
motion players, all with speed 1.0 and integer frame values, which is how "one animation
frame per game frame" looks from memory.

So the third word changes the constructor's `lui v0, 0x3f80` at `0x00137738` to `0x3f00`:
every motion player is born with a speed of 0.5, and at 60 steps a second animations play
at the same real rate as at 30. Blends also count down by `speed`, so transition lengths
keep their wall-clock duration too.

## The measurement

All runs are PCSX2 2.8.1 at 2x internal resolution, from one savestate on the main street
of Amahara with nobody hostile nearby. The emulator ran at full speed in every run: each
3.00 s hold of the left stick spanned exactly 180 vblanks on the `0x002EE494` counter. The
patch words are data or run-once code, so each run loads the state and writes them over PINE
before the walk; screenshots are `ScreenshotSize = 2`, 1280x896.

| Run | interval | FPS const | anim speed | frames in 3 s | where the walk ended |
|---|---|---|---|---|---|
| stock | 2 | 30 | 1.0 | 90 | between the two street lanterns |
| unlock only | 1 | 60 | 1.0 | 180 | at the town gate, twice as far |
| full patch | 1 | 60 | 0.5 | 180 | between the two street lanterns |

Greyscale mean-squared difference between the end frames:

| Pair | MSE |
|---|---|
| stock vs full patch | **165** |
| stock vs unlock only | 1464 |
| full patch vs unlock only | 1453 |

The 165 that remains is NPCs and animation phase; the same camera framing, the same spot on
the street. The savestate memory-diff method used on Etheria was tried first and abandoned
here: the floats it selected from the stock walks read a median displacement of 0 in every
60 fps run, which the screenshots show is wrong, so the diff was measuring something
camera-relative rather than the world. Pixels were the honest instrument this time.

Before the animation lever was found, the user played the unlock-only build and reported
double speed by eye; the FPS constant set from boot (a real patched launch, verified by
reading the words back) made no difference to that. That report is what turned this from a
one-word patch into a three-word one.

## What the patch does not correct

Anything stepped per frame outside the animation system now runs twice as fast in real
time: camera easing, screen fades, particle lifetimes and any UI motion that counts frames
without going through the FPS constant. `0x001CEC20` adds `16 * FPS / 30` per frame to three
colour channels, which at 60 is twice the increment at twice the rate; it is a fade and it
will be quick. Motion-keyed events that test the integer frame (`int(frame) == N`) will see
a fractional clock now, so a footstep sound or a hit window keyed that way could trigger on
two consecutive steps. None of this was measured; it needs playing, and the description says
so in gentler words. Movies were not exercised.

## The patch

| Patch | Purpose |
|---|---|
| `001E1C34: 00C0582D -> 240B0001` | display setup passes a vsync interval of 1 instead of 2 - a frame every field |
| `002EDA00: 0000001E -> 0000003C` | the engine's frames-per-second constant reads 60, so frame-counted timers keep their length |
| `00137738: 3C023F80 -> 3C023F00` | motion players are constructed with a clock speed of 0.5 instead of 1.0, so animation and the movement driven by it keep their pace |

All three are `place=0`: the first two are consumed at boot, and the third is a constructor
that runs each time a character is created, so it must be in place before the first one is.
A stock savestate loaded into a patched session brings back its own 30, 2 and 1.0 with it;
play from the memory card save instead.

## Notes for next time

- `PostMessage` pad input for the arrow keys needs the extended-key bit (`lParam` bit 24) as
  well as the scan code; without it the D-pad is silently dropped while letter keys work,
  which looks like a menu ignoring you.
- PINE `SaveState`/`LoadState` with a slot argument both work on 2.8.1 with this game, so the
  user's savestate slot can be left alone and the A/B written to other slots.
- The tutorial fight kills a scripted player quickly; drawing the sword and attacking makes
  the thugs flee, fleeing on foot does not.
