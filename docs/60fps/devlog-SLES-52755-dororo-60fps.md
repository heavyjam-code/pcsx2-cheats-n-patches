# Devlog: 60 FPS for Blood Will Tell - Tezuka Osamu's Dororo (SLES-52755)

Record of how the `[60 FPS]` group in
[`patches/SLES-52755_D781869F.pnach`](../../patches/SLES-52755_D781869F.pnach) was made.

Target: Sega / Red Entertainment (2004), PAL retail as the "Undub 28-Aug-2021" build, boot ELF
`SLES_527.55` (4,199,400 bytes), loaded at `0x00140000`, entry `0x00140008`, `$gp = 0x0053CEF0`.
Compiler string `MW MIPS C Compiler (2.4.1.01)`. No `.sndata`/`SNR1` symbol table, so everything
below was hand-mapped.

The patch is five words: two to unlock the frame rate, three to keep the pre-rendered movies from
strobing once it is unlocked. All five are `place=0`, so it needs a restart.

## The CRC is not the one PCSX2 ships a patch for

This undub's ELF CRC is **`D781869F`**. The stock PAL release is `D78D3D1F`, and that is the
serial+CRC PCSX2 bundles a `[Widescreen 16:9]` and a `[50/60 FPS]` group for in
`resources/patches.zip`. The undub changed the ELF, so **none of the bundled groups load on this
disc** - which is why this file exists at all.

The code, however, did not move. Both addresses the bundled 50/60 FPS group writes to hold exactly
the instructions that group expects:

| Address | Word in this ELF | Disassembly | What the bundled patch does to it |
|---|---|---|---|
| `0x003D79CC` | `10400008` | `beqz v0, 0x3d79f0` | `bnez` in NTSC mode, left alone in PAL |
| `0x001B4108` | `3C033F80` | `lui v1, 0x3f80` (1.0f) | 8-bit write of `0x00` making it `0x3f00` (0.5f) |

so the undub looks like a data-only rebuild, and a `D78D3D1F` file carrying the same two words as
this one would very probably work. It is not shipped, because this repo does not ship a file for a
build it has not run - see [the bundled patch](#the-bundled-patch-and-why-this-one-differs).

## Where the 30 comes from

Two things, and both are one number.

### 1. The frame interval

The main loop is at `0x00142400` and is three instructions long:

```
00142400  addiu sp, sp, -0x10
00142408  jal   0x1b4890          ; end of frame: flush, request a swap, wait
00142410  jal   0x1422f0          ; the frame's work: update the world, draw it
00142418  b     0x142408          ; forever
```

`0x001B4890` calls the GS driver's frame-boundary wait at `0x003D78E0`, handing it a pointer to the
vblank-wait routine (`0x0016FD10`) in `$a0`:

```
003d78f0  jalr s0                 ; wait one vblank
003d78f8  lw   a0, -0x14(gp)      ; vsyncCounter   0x0053CEDC
003d78fc  lw   v1, -0x1c(gp)      ; lastFrameVsync 0x0053CED4
003d7900  lw   v0, -0x10(gp)      ; frameInterval  0x0053CEE0
003d7904  addu v0, v1, v0         ; target = last + interval
003d7908  sltu at, a0, v0
003d790c  beqz at, 0x3d7940       ; cur >= target -> done
003d7918  jalr s0                 ; else wait another vblank and re-test
003d7978  sw   v1, -0x1c(gp)      ; last = cur
```

The same `frameInterval` gates the buffer swap itself, in the VBLANK handler at `0x003D7A40`:

```
003d7a54  lw   v1, -0x28(gp)      ; lastSwapRequest 0x0053CEC8
003d7a58  lw   v0, -0x140(gp)     ; swapRequests    0x0053CDB0  (++ once per frame, 0x003D7A00)
003d7a5c  beq  v1, v0, return     ; nothing new to show
003d7a64  lw   a0, -0x20(gp)      ; lastSwapVsync   0x0053CED0
003d7a68  lw   v1, -0x10(gp)      ; frameInterval
003d7a70  addu v1, a0, v1
003d7a74  sltu at, v0, v1
003d7a78  bnez at, return         ; too early
```

`frameInterval` is **2**, live, in both video modes. One frame per two vblanks: 25 fps on the PAL
raster, 30 fps on the NTSC one.

It has exactly one writer in the whole ELF, `0x003D9204`, inside the GS driver's init at
`0x003D8BD0`, where it arrives as the fourth argument (`$a3`, spilled to `0xec(sp)` at
`0x003D8C1C`) and is read out of a display-config struct by both callers (`0x003D8924`,
`0x003D8A1C`).

The driver also carries a field-parity block - `if (flags & 2) wait until the vsync counter is even`
at `0x003D7940`, with a partner in the second waiter at `0x003D8060`. Its flag word `0x01F536DC`
reads **0** in every state sampled (boot, menus, gameplay, movie playback), so that path is dead on
this disc and no patch has to fight it.

### 2. The logic rate, which is half the refresh rate

`SetLogicRate(hz)` at `0x001B40D0` accepts only 50 or 60 (anything else is forced to 50) and then
builds a ten-word timing table at `0x01E5D620` from `R = hz / 2`:

```
001b40d0  addiu a1, zero, 0x32    ; 50
001b40d4  beq   a0, a1, ok
001b40d8  addiu v1, zero, 0x3c    ; 60
001b40dc  beq   a0, v1, ok
001b40e4  move  a0, a1            ; else 50
001b40e8  bgez  a0, 0x1b40f8
001b40ec  sra   v1, a0, 1         ; <-- R = hz / 2
001b4100  sw    v1, -0x29e0(at)   ; 0x01E5D620
```

| Address | Value | Stock at 60Hz | Patched at 60Hz |
|---|---|---|---|
| `0x01E5D620` | `R`, as an int | 30 | 60 |
| `0x01E5D624` | `(float)R` | 30.0 | 60.0 |
| `0x01E5D628` | `1 / R` - seconds per logic step | 0.0333 | 0.0167 |
| `0x01E5D62C` | `60 / R` | 2.0 | 1.0 |
| `0x01E5D630` | `30 / R` | 1.0 | 0.5 |
| `0x01E5D634` | `R / 30` | 1.0 | 2.0 |
| `0x01E5D638` | `980 / R^2` - gravity per step squared | 1.0889 | 0.2722 |
| `0x01E5D63C` | `R * 60` | 1800 | 3600 |
| `0x01E5D640` | `R * 3600` | 108000 | 216000 |
| `0x01E5D644` | `R * 86400` | 2592000 | 5184000 |

`0x01E5D620` alone is read from **393 sites** across the ELF, as an int (`lw`) and as a float
(`lwc1` then `cvt.s.w`). This is the number the whole game measures time in.

Its callers are the boot default at `0x001B42D0` (`a0 = -1`, so 50) and the TV-setting apply block
at `0x001B48C0`, which reads the requested mode from `0x0053C6AC` and calls `SetLogicRate(50)` with
a 512-line screen for PAL, or `SetLogicRate(60)` with a 448-line screen for NTSC.

### The TV setting is the game's own 60Hz switch

This PAL disc asks at boot. `SetVideoMode(mode)` is `0x001B3FF0` (stores the mode at `0x0053C6AC`,
raises a pending byte at `0x0053C6A8`); the "TV setting" screen calls it with 2 (NTSC) at
`0x001C43DC` and 3 (PAL) at `0x001C4504`, then shows *Would you like to play the game in this TV
setting?* with a countdown, and `0x001B48C0` applies the choice.

So no video-mode patch is needed here - unlike Global Defence Force, this port ships a working 60Hz
mode and only needs the frame rate unlocked inside it. Picking 50 Hz gives 50 fps at the same game
speed, because everything is expressed in `R` and `R` follows the refresh rate.

## The patch

```
patch=0,EE,001b40ec,word,0080182d      sra v1, a0, 1     ->  daddu v1, a0, zero
patch=0,EE,003d91ec,word,24030001      lw v1, 0xec(sp)   ->  addiu v1, zero, 1
patch=0,EE,002790cc,word,00000000      beqz a0, 0x2790f8 ->  nop
patch=0,EE,002790ec,word,af96fc38      jal 0x3d25d8      ->  sw s6, -0x3c8(gp)
patch=0,EE,002790f0,word,00000000      lui a2, 1         ->  nop
```

The first makes `R = hz` instead of `hz / 2`, so the *whole* timing table is rebuilt consistently
for the new rate - one word, and every one of those 393 readers gets a coherent number. The
`bgez`/`sra` pair around it is a signed divide by two whose taken path is the delay slot, and `a0`
is only ever 50 or 60, so replacing the delay slot is enough.

The second forces the driver init's frame-interval argument to 1 before it is stored, which is
better than writing `0x0053CEE0` directly: the init is the only writer, so the value can never be
put back, and the patch survives the driver being re-initialised.

The last three are the movie fix, and they are [their own story](#the-movies-and-the-hold-slot-the-game-never-fills).

`place=0` throughout. The GS driver init runs in the first second of boot, well before a `place=1`
line would first fire - the same lesson as Ys VI's frame-rate constant at `0x00217624`. One
consequence worth knowing: a savestate carries EE RAM, including the ELF image, so loading a state
that was saved before the group was ticked puts the stock words back and the game runs unpatched
until it is rebooted. PCSX2 does not re-apply `place=0` lines after a state load.

Verified after a cold boot: all five words read back patched, the ten words at `0x01E5D620` match
the 60-based table bit for bit, and the frame rate is 60.00.

## The measurement

PCSX2 2.8.1, emulator at 100%, 4x internal resolution, PINE for memory. Frame rate is counted as
transitions of `lastFrameVsync` (`0x0053CED4`); the raster rate is counted off `vsyncCounter`
(`0x0053CEDC`), which the patch does not touch and which therefore doubles as the real-time clock.

| Scene | stock | patched |
|---|---|---|
| boot, PAL 50Hz default | 25 fps | 50.00 fps |
| menus and gameplay, 60Hz TV setting | 30.00 fps | 60.00 fps |
| `frameInterval` / `R` | 2 / 30 | 1 / 60 |

### Game speed

All runs load the same savestate - the first village, out in the open, tutorial overlay up - and
hold forward for the same number of **vblanks**, not the same number of frames, so both sides get
the same amount of real time whatever the frame rate. The configuration is applied by writing the
ten timing words and the interval over PINE, which is exactly what the two patched instructions
produce and lets both sides run identical code:

| run | vblanks | game frames | wall clock | emulator |
|---|---|---|---|---|
| 60 fps, walking | 180 | 180 | 3.00 s | 100% |
| 60 fps, idle | 180 | 179 | 2.99 s | 100% |
| 30 fps, walking | 180 | 89 | 2.99 s | 100% |
| 30 fps, idle | 180 | 89 | 2.99 s | 100% |

Diffing EE memory against the base state gives every value the walk moved and the idle runs left
alone. Over a **ten-second** walk (600 vblanks):

- 200 homogeneous position vectors (qword-aligned, `w == 1.0f`) tracked in all three states.
  Displacement ratio 60 fps : 30 fps, **median 1.0000**. The largest travels 74,710 units and the
  two runs end **67 units apart - 0.09% of the distance walked**. Median end-state separation across
  all 200 is 0.16% of travel.
- Across all 9,750 changed floats the ratio histogram is a single spike: **87.8% within +/-5% of
  1.0**, with **0.0% near 0.5 and 0.1% near 2.0**. Nothing in the game state advances at half or
  double rate; the tails are dust particles and other chaotic effects, which diverge between any two
  runs anyway.

That is the whole argument for why this is safe. The engine runs one logic step per drawn frame and
counts every duration in steps, so making it draw twice as often is correct exactly as long as the
steps-per-second number moves with it - and the memory says it does.

### The one timer that is not on the clock

The TV-setting confirmation is a raw frame count - `addiu v0, zero, 0x95` (149) at `0x001C43E4`,
stored into the screen's countdown field. It is the only frame-counted timer found, and the patch
halves it: measured from PCSX2's own `Mode Changed` log lines, the *Would you like to play the game
in this TV setting?* prompt times out after **5.00 s** stock and **2.51 s** patched. Still enough
time to answer, but it is a real change and it is in the group's description.

## The movies, and the hold slot the game never fills

Unlocking the frame rate alone breaks the four pre-rendered movies - `\SFD\op_eu.sfd`, `pr1_eu.sfd`,
`pr2_eu.sfd`, `end_eu.sfd`, each with a `_p` variant, indexed from a 28-byte-per-entry table at
`0x004821E8`. They are CRI Sofdec streams (the ELF carries the whole `mwPly*` assertion-string set,
and the Sofdec/ADX logo shows before the opening), they are 30 fps files, and at 60 fps every second
presented frame of a movie comes out **pure black**.

Measured from a savestate taken on the Sofdec logo screen, running the opening movie for the same
600 vblanks each way and sampling ten screenshots per run:

| interval | logic rate `R` | black frames out of 10 |
|---|---|---|
| 2 | 30 | 0 |
| 2 | 60 | 0 |
| 1 | 30 | 7 |
| 1 | 60 | 5 |

So it tracks the **presentation interval**, not the timing table; `R` is irrelevant to it. The movie
itself plays at the right speed - sampling both runs at 3, 7, 11, 15, 19, 23, 27 and 31 seconds, the
frames that are not black are **bit-identical** to the 30 fps run at the same timestamp. Mean
luminance on the bad frames is exactly 0.00 across the whole picture, so the buffer really is empty
rather than merely missing the movie.

### Finding the movie code

The 96 `mwPly*` assertion strings each have exactly one code reference, which turns the CRI library
into a labelled map for free: resolve each string's referencing instruction back to its function
entry and the whole Sofdec API is named. Two of those functions are called from outside the library:

| Function | Entry | Called from |
|---|---|---|
| `mwPlyGetCurFrm` | `0x0016D7F0` | `0x002790C0` |
| `mwPlyRelCurFrm` | `0x0016E2A0` | `0x00279350` |

Both call sites are in one function, `0x00279000`, which is the movie's per-frame draw, and it sits
in a self-contained movie module at `0x00278000`-`0x0027A000` whose state lives in the `$gp`
small-data area (`gp-0x3d0` state, `gp-0x320` handle, `gp-0x3e0`/`gp-0x3d8` the 512x448 picture
size). Its top reads:

```
002790c0  jal  mwPlyGetCurFrm       ; a0 = handle
002790c4  addiu a1, sp, 0x280       ; out
002790c8  lw   a0, -0x3c8(gp)       ; the hold buffer            0x0053CB28
002790cc  beqz a0, 0x2790f8         ; none configured -> straight to the draw test
002790d0  lw   s6, 0x280(sp)        ; s6 = the picture we just got, or NULL
002790d4  bnez s6, 0x2790e8         ; got one -> keep it
002790dc  b    0x2790f8
002790e0  move s6, a0               ; else fall back to the held one
002790e8  move a1, s6
002790ec  jal  0x3d25d8             ; memcpy16(dst = hold buffer, src = picture,
002790f0  lui  a2, 1                ;          0x10000 qwords = 1 MB)
002790f4  nop
002790f8  beqz s6, 0x279368         ; nothing to draw -> skip the frame entirely
```

and its tail releases the picture only when one was actually fetched:

```
00279340  lw   v0, 0x280(sp)
00279344  beqz v0, 0x279358         ; nothing fetched -> nothing to release
00279350  jal  mwPlyRelCurFrm
```

That is the whole story. The game fetches, draws and immediately releases each picture, so
`mwPlyGetCurFrm` returns NULL on every frame where the decoder has not produced a new one - one in
two at 60 fps - and with nothing fetched and nothing held, `beqz s6` at `0x002790F8` skips the draw
and the frame is presented empty.

**The engine already has the fix in it.** `0x002790E0` re-draws a held picture when the fresh one is
missing; it is simply never reached, because the hold buffer at `gp-0x3c8` is NULL. Live, during
playback, `0x0053CB28` reads 0.

That global has one writer, a one-instruction public setter at `0x00279CE0`
(`jr ra; sw a0, -0x3c8(gp)`), called by client scenes rather than by the movie module itself:

| Caller | What it does |
|---|---|
| `0x001DFF00` | allocates 1 MB (`0x00142EC0(heap 0x00548830, 0x00100000)`) and passes it - but only if the scene's mode `s0 == 3`, tested at `0x001DFED4` |
| `0x001E0A80` | frees it and passes NULL |
| `0x0030CE2C` | a second class, allocates 1 MB unconditionally |
| `0x0030CEA0` | its free path |

The scenes that play the boot and story movies are in neither class, so nothing ever calls the
setter: watched over a whole cold boot including the opening movie, `0x0053CB28` never leaves 0.
NOPping the `s0 == 3` test at `0x001DFED4` changes nothing for the same reason - that constructor is
not the one in use.

### The fix: hold the picture, not a copy of it

Rather than hunting for somewhere to allocate a megabyte from a pnach, point the hold slot at the
picture itself. Three words:

```
002790cc  nop                       ; was beqz a0, 0x2790f8 - always consider the held picture
002790ec  sw   s6, -0x3c8(gp)       ; was the 1 MB memcpy - remember this picture instead
002790f0  nop                       ; was its length argument
```

which turns the block into: if a fresh picture arrived, remember it and draw it; if not, draw the
one remembered last frame. `a1` is clobbered by the dead `move` at `0x002790E8` and reassigned at
`0x00279110`, so nothing else has to change, and on the very first frame both are NULL and the
stock skip still applies.

The obvious objection is that the picture is released back to the decoder pool at the end of the
frame it arrived on, so the second draw reads a buffer the decoder owns again. In practice the pool
is several frames deep and the reuse never lands inside the 16 ms the picture is needed for:

- 21 frames sampled across the whole opening movie at 60 fps: **0 black, 0 torn**. A row-profile
  seam detector (largest row-to-row luminance step, as a z-score against the frame's own row noise)
  gives a median of 8.9 and a maximum of 26.8 against a stock-30 control's 8.8 and 14.6; the one
  outlier is a step in the last five rows of the picture, i.e. the frame's own bottom edge.
- 10 further marks sampled in both configurations from the same savestate: 0 black on either side,
  and mean luminance matching stock to within the phase of one movie frame.
- A cold boot with the shipped file, sampling ten frames of the opening: one black frame, which is
  the movie's own cut - the frames either side of it are the "Production Design" credit card and the
  sky shot that follows it.

Against the unpatched 60 fps run's 50-70% blank frames, that is the fix working.

Ruled out on the way:

- **Not a screenshot artifact.** Every gameplay capture at 60 fps, including the ten-second walk end
  frames, is a full picture; only movie frames came back black.
- **Not the field-parity block.** `0x01F536DC` is 0 during movie playback, same as everywhere else.
- **Not the display-buffer choice.** The swap handler picks the buffer from the swap-request counter
  (`0x003D7BC0` passes `gp-0x140` to `0x003D7570`), a clean per-frame toggle; the `FIELD`-derived
  index computed at `0x003D7A98` is only used on the `flags & 4` path, which is dead here.
- **Not worth gating the interval on a "movie playing" flag.** Diffing gameplay, the movie menu, the
  Sofdec logo and two frames of playback for a byte or word set only while a movie runs gave 49 byte
  and 104 word candidates, none with a resolvable code reference; the most promising static
  (`0x0042DE18`, 0 everywhere and 2 in both playback snapshots) turned out to be a scratch word that
  toggles many times a second. Holding the picture is both smaller and better - the movie stays at
  60 Hz presentation with repeated frames instead of dropping the whole display back to 30.

## The bundled patch, and why this one differs

`resources/patches.zip` carries `SLES-52755_D78D3D1F.pnach` with a `[50/60 FPS]` group by
PeterDelta. It does not load on this disc (wrong CRC), but it is worth reading, because it reaches
the same two levers by a different route:

```
patch=1,EE,203D79CC,extended,16400008     ; beqz -> bnez in the vblank counter handler
patch=1,EE,E0010003,extended,00421A88     ; if PAL,
patch=1,EE,203D79CC,extended,10400008     ;   put it back
patch=1,EE,01E5D620,extended,0000003C     ; 8-bit write: R = 60
patch=1,EE,001B4108,extended,3C033F00     ; 8-bit write: 1.0f -> 0.5f inside SetLogicRate
patch=1,EE,E0010003,extended,00446F60     ; if PAL,
patch=1,EE,01E5D620,extended,00000032     ;   R = 50
```

Two things about it. First, both `0x01E5D620` and `0x001B4108` are written with a **leading `0`**,
which in an `extended` address means an 8-bit write, not the 32-bit one the data column reads like.
For `0x001B4108` that happens to be exactly right - only the low byte of `3C033F80` has to change to
make `3C033F00` - but for `0x01E5D620` it means the int rate is stamped over on every vsync *after*
`SetLogicRate` has already derived the rest of the table from 30, so the int and the float
(`0x01E5D624`, still 30.0) disagree for the whole session and the derived constants only come out
right because the separate `0.5f` edit happens to halve them. The same "the leading digit is the
write width" trap is on record in this repo from a bundled Champions of Norrath group.

Second, it does not touch the frame interval at all. It flips the parity of the vblank counter
handler at `0x003D79CC` instead, which only works because of how PCSX2 reports the GS `FIELD` bit -
the same class of emulator-quirk dependency noted for the bundled Sword of Etheria patch. This patch
sets `frameInterval` at its single writer, which is what the engine actually reads, and derives `R`
from the real refresh rate at its single source, so the two numbers stay consistent with each other
and with the video mode the player picked.

## Address summary

| Address | What |
|---|---|
| `0x00142400` | main loop: frame end, then update, forever |
| `0x001422F0` | the frame's work; bumps a frame counter at `0x0053C68C` |
| `0x001B4890` | frame end: flush, request swap (`0x003D7A00`), wait (`0x003D78E0`), apply pending video mode |
| `0x003D78E0` | frame-boundary wait; reads `frameInterval` at `0x003D7900` and `0x003D7928` |
| `0x003D79B0` | VBLANK handler that advances `vsyncCounter` and keeps its parity on the GS `FIELD` bit |
| `0x003D7A40` | VBLANK handler that performs the buffer swap; reads `frameInterval` at `0x003D7A68` |
| `0x003D7FC0` | a second waiter with its own `last` at `0x0053CED8`; only caller is `0x003D7804` |
| `0x003D8BD0` | GS driver init; **`0x003D91EC` is the patched word**, `0x003D9204` stores the interval |
| `0x001B40D0` | `SetLogicRate(hz)`; **`0x001B40EC` is the patched word** |
| `0x00279000` | the movie's per-frame draw; **`0x002790CC`, `0x002790EC` and `0x002790F0` are the other three patched words** |
| `0x00279CE0` | `SetMovieHoldBuffer(void*)`, the setter nothing in the movie scenes calls |
| `0x0053CB28` | the hold slot - NULL stock, the last drawn picture with the patch |
| `0x0016D7F0` / `0x0016E2A0` | `mwPlyGetCurFrm` / `mwPlyRelCurFrm` |
| `0x001B3FF0` | request a video mode; applied by `0x001B48C0` |
| `0x001C43DC` / `0x001C4504` | the TV-setting screen asking for NTSC / PAL |
| `0x0053CEE0` | frame interval (2 stock, 1 patched) |
| `0x0053CEDC` | vblank counter - the real-time clock for every measurement above |
| `0x0053CED4` | vblank count at the last presented frame - the frame-rate probe |
| `0x01E5D620` | logic steps per second; 393 readers |
