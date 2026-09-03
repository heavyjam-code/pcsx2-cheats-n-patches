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
one-word patch into a three-word one, and the second play-test (jumps) into a sixteen-word one, and the third into forty.

## The jump

The first play-test came back with walking and combat right and jumps at double speed. A
jump is the one movement here that is not root motion: it is a small vertical physics
integrator on the body object (`character + 0x1A0`), sampled every vsync over PINE with the
player at `0x01621620`:

| Body field | Meaning |
|---|---|
| `+0xB0/B4/B8` | position |
| `+0xD0/D4/D8` | next position, `pos + vel`, written by `0x001CBE90` (vector add at `0x001CBF6C`) |
| `+0xF0/F4/F8` | velocity |
| `+0x08` bit 3 | airborne |

Reading `vy` every frame of a stock jump gave, to four decimals, `vy = 0.8 vy - 0.01`
while rising and `vy = 1.2 vy - 0.01` while falling, with `y += vy` after each update. That
is one rule, `vy -= 0.2 |vy| + 0.01`, and it lives in `0x001CBF90` (called once per frame
from the body update `0x001CC680`, only while airborne):

```
001CC0B8  lui  v0, 0x3e4c / ori 0xcccd     ; 0.2
001CC0C4  jal  0x136e80                    ; fabs(0.2 * vy)
001CC0CC  lui  v0, 0x3c23 / ori 0xd70a     ; 0.01
001CC0E0  sub.s f1, f2, f1                 ; -|0.2 vy| - 0.01
001CC0E4  add.s f0, f0, f1                 ; vy += that
```

with a second branch under body flag `0x40000` using 0.15625 and 0.004 (`0x001CC074`,
`0x001CC088`). The launch is the `flag & 4` branch of the velocity setter `0x001CB2B0`:
`vy = 0.36` (`0x001CB328`, `lui 0x3eb8 / ori 0x51ec`), found by zeroing drag and gravity and
reading the value that stayed put; its two sibling branches launch at 0.4 and 0.284 for other
actions. Stock, then, is: `vy = 0.36`, and each frame decay then integrate - `0.278, 0.4904,
0.6503, ...` - apex 0.9699 on frame 9, 20 frames in the air.

At 60 steps a second the same rule runs twice as often, and the animation clock does not
touch it. The exact conversion of `v' = a v - b` to half steps is `a' = sqrt(a)`,
`b' = b / (1 + a')`, but the rule has one drag constant serving both `a = 0.8` and `a = 1.2`,
and the launch is decayed once before it is first integrated, so the constants were fitted
instead: a grid search over launch, drag and gravity against the stock curve sampled at the
30 fps instants, weighting the flight length, gave

| | stock (per 1/30 s) | patch (per 1/60 s) | words |
|---|---|---|---|
| launch | 0.36 | 0.164 | `001CB328/2C: 3E27EF9E` |
| launch, sibling branches | 0.4, 0.284 | 0.182, 0.129 (same ratio) | `001CB344/48: 3E3A9876`, `001CB358/5C: 3E047B9C` |
| drag | 0.2 | 0.1025 | `001CC0B8/BC: 3DD1EB85` |
| gravity | 0.01 | 0.0025 | `001CC0CC: lui 0x3b23` (ori unchanged) |
| alt-mode drag, gravity | 0.15625, 0.004 | 0.078125, 0.00104 | `001CC074: lui 0x3da0`, `001CC088/90: 3A88A2CB` |
| air steering | 0.004 | 0.001 | `001CBA98: lui 0x3a83` |

Measured in-game with all of it applied over PINE at 60 fps: apex **0.975** (stock 0.970),
39 half-steps in the air by the model and 35 sampled after the first read caught it mid-rise
(stock 20 frames). The alt-mode pair uses the same arithmetic and was not exercised.

That fixed the standing jump and left the running jump catapulting forward. Horizontal is
two terms. The launch is the length of the body's root-motion delta (`+0xE0`, the vector
the animation moved the character by this frame) along the facing direction (`+0x110`) -
`0x001D1F60` - and that delta is already half-size under the animation clock (0.0548 per
step patched, 0.1094 per frame stock, the same ground per second), so the launch takes care
of itself: 0.0431 patched, 0.0860 stock. The other term is air steering: `0x001CBA70`
normalises the facing direction, scales it by `0.004` (`lui 0x3b83 / ori 0x126f` at
`0x001CBA98`) and adds it to `vel.xz` every step while body flag `0x8000` is set, which is
why stock `vz` climbs 0.086 -> 0.154 across the flight. A per-frame acceleration halves
twice going to half steps (half the velocity, twice the steps), so `0.004 -> 0.001`, one
`lui`. Forward jump measured from the launch frame: **2.12** patched vs 2.03 stock, 37 vs 36
vsyncs in the air. Without that word it was 4.40.

## What the patch does not correct

Anything stepped per frame outside the animation system and the jump integrator now runs
twice as fast in real time: camera easing, screen fades, particle lifetimes and any UI motion
that counts frames without going through the FPS constant. The small scripted hops in
`0x001C9960` (types `0x38`-`0x3A`, launch 0.03-0.125) go through the same integrator and get
the corrected drag and gravity but keep their full launch, so they rise a little higher. `0x001CEC20` adds `16 * FPS / 30` per frame to three
colour channels, which at 60 is twice the increment at twice the rate; it is a fade and it
will be quick. Motion-keyed events that test the integer frame (`int(frame) == N`) will see
a fractional clock now, so a footstep sound or a hit window keyed that way could trigger on
two consecutive steps. None of this was measured; it needs playing, and the description says
so in gentler words. Movies were not exercised.

## Third pass: hops, fades, water, particles

The third play-test listed camera easing, fades, effects and the evade hops. What was found:

- **Scripted hops** (`0x001C9960`, action types `0x38`-`0x3B`): a direct velocity setter, no
  fit needed. Horizontal `0.015625` -> `0.0078125` at `0x001C99EC`, `0x001C9AB4` (negative
  for the backward hop) and `0x001C9B48`; vertical launches `0.03125*(n+1)`, `0.125` and
  `0.53125*0.03125*(n+1)` scaled by the same 0.456 the jump fit produced, at `0x001C9A0C`,
  `0x001C9AD4`, `0x001C9BBC` and `0x001C9C40`. All single `lui` words, so the values are
  16-bit-rounded (0.01422 for 0.01424, 0.0569 for 0.05694).
- **Colour fade** `0x001CEC20`: the one site that adds `16 * FPS / 30` per frame; with
  FPS = 60 that is twice the increment at twice the rate. `16.0 -> 4.0` at `0x001CEC6C`.
- **Screen fades** were already right: the general stepper `0x001E0770` counts frames
  against the FPS constant (a fade is `FPS` frames long, one second either way), and every
  one of its ~30 "start fade" callers only fills in the four globals at `0x002EE6B4`. Nothing
  to patch.
- **Water**: `0x00158340` scrolls the river texture by `0.002` per frame (`gp-0x747c`,
  wrapping at 1.0) - halved at `0x00158378`. Its 30-frame texture cycle (`gp-0x7480`,
  `slti 0x1e`) indexes a 30-entry table, so slowing that counter needs code, not a
  constant, and it still cycles at 2x.
- **Particles** (`particle`/`kemuri` classes, vtables `0x002EC750`-`0x002EC810`, updates
  `0x0023F820`, `0x00241290`, `0x002414A0`, `0x00241670`, `0x00241A90`, `0x00241D80`): each
  update adds fixed per-step amounts - a `0.1`-scaled velocity, `+0.01 * sin` drift,
  `+0.002`/`+0.005`/`+0.0001` growth, `+0.001`/`+0.1` rise. All fifteen rate constants are
  halved (each is a `lui` word; thresholds such as the `0.3` compare at `0x0023F8E0` are
  left alone). Lifetimes are integer frame counters inside the same updates, so a particle
  now moves at the stock rate but lives half as long. The gate-stub alternative (run the
  particle update every other presented frame from a 6-word stub in the text padding at
  `0x002BC7CC`) was built and tried, but the class update slot also draws, so gating it
  makes particles flicker; it is not used.
- **Camera**: not corrected. The gameplay camera is applied by `0x0012EBD0` from the scene
  update at `0x001DD710` (via `0x00166040` / `0x00165430`), and none of the modules read so
  far hold an easing constant next to anything camera-shaped; the eye vector only exists
  inside the display context (`+0x260`). It settles twice as fast at 60 fps.

## The patch

| Patch | Purpose |
|---|---|
| `001E1C34: 00C0582D -> 240B0001` | display setup passes a vsync interval of 1 instead of 2 - a frame every field |
| `002EDA00: 0000001E -> 0000003C` | the engine's frames-per-second constant reads 60, so frame-counted timers keep their length |
| `00137738: 3C023F80 -> 3C023F00` | motion players are constructed with a clock speed of 0.5 instead of 1.0, so animation and the movement driven by it keep their pace |
| `001CB328/2C`, `001CB344/48`, `001CB358/5C` | jump launch velocities 0.36 / 0.4 / 0.284 -> 0.164 / 0.182 / 0.129 |
| `001CC0B8/BC: 0.2 -> 0.1025`, `001CC0CC: 0.01 -> 0.0025` | air drag and gravity per step, fitted to the stock curve |
| `001CC074: 0.15625 -> 0.078125`, `001CC088/90: 0.004 -> 0.00104` | the same for the body's alternate physics mode |
| `001CBA98: 0.004 -> 0.001` | in-air steering acceleration per step |
| `001C99EC`, `001C9AB4`, `001C9B48`, `001C9A0C`, `001C9AD4`, `001C9BBC`, `001C9C40` | scripted hop launches: horizontal halved, vertical x0.456 |
| `001CEC6C: 16.0 -> 4.0` | the one `x * FPS/30` per-frame colour increment |
| `00158378: 0.002 -> 0.001` | water texture scroll per step |
| `0023F838` ... `00241DBC` (15 words) | particle per-step rates halved |

All lines are `place=0`: the first two are consumed at boot, the constructor runs each time a
character is created, and the physics words are plain code in per-frame functions.
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
