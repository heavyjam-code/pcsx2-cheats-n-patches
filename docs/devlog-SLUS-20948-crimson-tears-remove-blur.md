# Devlog: Remove Blur/Bloom for Crimson Tears (SLUS-20948)

How [`patches/SLUS-20948_D31904C2.pnach`](../patches/SLUS-20948_D31904C2.pnach) was made. Symptom: heavy haze and edge ghosting over the whole image, much worse at upscaled internal resolutions. PCSX2's GameDB already applies `halfPixelOffset: 4` + `nativeScaling: 4` ("Aligns/Fixes post effects") for this game and the ghosting survives them.

Target: Capcom/DreamFactory brawler (2004), boot ELF `SLUS_209.48`, ELF CRC `D31904C2` (PCSX2 CRC = XOR of every little-endian u32 of the whole file — verified byte-identical against the record for this exact ISO in PCSX2's `cache/gamelist.cache`). The 2021 undub keeps the retail ELF, so the patch works for stock USA discs too. Tested on PCSX2 2.8.1, Vulkan, 3x scale. Single loadable segment maps `file_offset = va - 0x100000 + 0x80`; `$gp = 0x3A03F0`.

## Finding the effect (map of the ELF)

The binary keeps C++ RTTI names — `strings` alone gives the engine's class list (`drf::` = DreamFactory framework, `drf::ct::` = Crimson Tears game code). Two post-process systems exist:

| Address | What it is |
|---|---|
| `0x337520` | `CBlurTask` ctor — registers task `"BLUR"`, news a 0x90-byte radial-blur state (5 layers, decay weights 2.3/0.9/0.3/0.15/0.5, color 0x80808080), pointer kept at `gp-0x76B8` = `0x398D38` |
| `0x1AC078/0x1AC128` | scene-renderer arbiter: when `blur->enabled`, starts a named render layer at priority 0x14A, else stops it (event blur — dashes/skills set the flag at 4 sites) |
| `0x32A280` | `CGlowTask` ctor — registers task `"GLOW"`, vtable `0x398020` |
| `0x329E70` | `CGlowTask::update` — ping-pong lerps two RGBA sets (~±0.1/frame) into the glow color; gated on `task+0xA8` |
| `0x32A200` | `CGlowTask` draw thunk: `j 0x32A550 ; lw a0,0x90(a0)` — the **only** entry into the glow renderer |
| `0x32A550` | `CGlow::draw`, 0x1020 bytes. Mostly unrolled; **one real loop** `0x32AE40..0x32B26C` |
| **`0x38BA40`** | **the blur tap table: 4 × `{s16 x, s16 y}` = `(0,0) (-1,0) (+1,0) (0,+1)`** |
| `0x1668B8` | display putter — also runs a PMODE dual-circuit soft filter (ALP=0x80). PCSX2's default anti-blur already neutralizes this, so it is not the culprit |

The bloom is a downsample pyramid: the loop runs `glow+0xA8` times, halving the working buffer each pass (`srl` at `0x32AE7C`/`0x32AE80`) and picking a tap offset with `index & 3` into the table at `0x38BA40`, which it writes into `glow+0x80/+0x84`.

Route to the code: find the RTTI/tag strings (`"GLOW"`, `"BLUR"`, `drf::ct::CGlowTask`), locate their typeinfo records via aligned-pointer scans, then find the constructor as the code that materializes the tag string / vtable address via `lui`+`addiu` pairs. A full `lui 0x1200` sweep (every GS privileged-register store) ruled out display-level causes first.

## Attempt 1 — kill the glow outright (SHIPPED, THEN REGRESSED)

`CGlow::draw` has exactly one entry, so `0x32A200` → `jr ra ; nop` severs the whole pass. That killed the ghosting and shipped.

**User feedback: "considerably darker".** They were right, and it is measurable — the glow is an *additive* pass, so removing it removes light:

| variant | mean luma | vs stock |
|---|---|---|
| stock | 70.35 | — |
| glow killed | 64.98 | **−7.6%** |

**Lesson: an effect that ghosts is usually also carrying real light. Killing it is a two-sided trade, and "it looks sharper" in a screenshot hides the loss.**

## Attempt 2 — zero the tap offsets

The root cause is the tap table, and it is a textbook upscaling failure: the game blurs by offsetting each pass **±1 native pixel**. At native 640×448 that is a sub-pixel-ish soft blur. At 3x internal resolution PCSX2 renders the same offset as **±3 screen pixels** — a hard, visible double image rather than a blur. That is exactly the "ghosting", and it is why GameDB's `halfPixelOffset`/`nativeScaling` fixes do not help: the offset is applied by *game logic*, not by the emulator's sampling.

Entry 0 is already `(0,0)`, so zeroing the other three collapses every tap onto the same position: the same number of accumulation passes run (light preserved) with no lateral spread (smear removed).

Measured live, same scene, same frame, glow contribution isolated as `stock − glowkilled`:

| metric | stock | zero-jitter | change |
|---|---|---|---|
| mean luma | 70.35 | 70.21 | **−0.2%** (brightness kept) |
| haze — glow light landing on dark pixels | 7.21M | 4.23M | **−41.3%** |
| bloom — glow light on bright pixels | 3.82M | 4.82M | **+26.3%** (tighter, stronger) |

So the light stays, the veiling glare that washes out blacks nearly halves, and the glow concentrates onto actual light sources. Visually: yellow hazard stripes go from smeared to crisp while the floor keeps its warm lighting, which the full kill drains away.

Safety: `0x38BA40` is referenced by **exactly one** instruction pair in the entire image (`0x32AE44/0x32AE4C`) and is never written by any store — pure const data feeding only this loop.

**User feedback: "I still see heavy glow around the pipes".** Also correct, and predicted by the same table: with the taps collapsed, the light that used to smear sideways now piles onto the source, so bloom on bright pixels went **+26.3%**. Screenshots of a railing in front of a bright window confirmed the glow still ate the rails.

## Attempt 3 — try to dim the glow instead (FAILED: not a usable knob)

`CGlow::draw` writes `0x80808080` as the sprite RGBA at four sites (`0x32AB64/0x32AB6C`, `0x32ADCC/0x32ADD0`, `0x32AEE4/0x32AEEC`, `0x32B248/0x32B24C`). Scaling all four looked like a clean intensity dimmer. It is not — `0x80` is GS's 1.0 point and the response falls off a cliff immediately below it:

| RGBA | mean luma over glow-off | bloom (bright px) |
|---|---|---|
| 0x80 (stock) | +4.85 | 4.90M |
| 0x60 | +0.62 | 1.44M |
| 0x40 | +0.12 | 0.81M |

One notch down throws away **87%** of the brightness contribution while the halo is still clearly visible — the worst of both. The pyramid depth (`glow+0xA8`, loop bound at `0x32B260`, patchable to `addiu v0,zero,N`) behaves more sensibly but only trades halo radius against light along the same curve.

**Lesson: the bloom's light and the bloom's halo are the same photons. No setting of this effect gives "bright but no bleed" — that has to come from outside the effect.**

## Attempt 4 — glow off, brightness restored outside the game (FINAL)

Since the glow cannot be made to give light without bleed, the answer is to remove it and put the light back with a tone curve, which has no spatial extent and therefore no bleed at all.

Modelled offline against the captured frames before touching the emulator (glow-killed frame, candidate curves applied in numpy, compared to the stock frame):

| correction | mean luma | vs stock | black% | clipped highlights |
|---|---|---|---|---|
| none (glow killed) | 65.10 | −4.95 | 9.66 | 0.00% |
| **gamma 1.08** | **70.87** | **+0.82** | 7.66 | **0.00%** |
| gain ×1.08 | 70.12 | +0.07 | 8.92 | 1.09% |
| lift +0.02 | 70.16 | +0.11 | 6.46 | 1.01% |

Gamma wins: it restores the midtones without clipping highlights or lifting blacks the way a flat offset does. PCSX2 exposes exactly this per game — **ShadeBoost Gamma, where the slider is `value/50`, so 54 = gamma 1.08.**

Measured in the running game, same savestate, patch loaded from file:

| | mean luma | black% |
|---|---|---|
| stock (glow on) | 70.05 | 8.84 |
| glow killed | 65.10 | 9.66 |
| **glow killed + Gamma 54** | **70.50** | **8.43** |

Brightness matched to within 0.6% of stock, blacks slightly *deeper* than stock, and no bloom anywhere: railings read as clean metal tubes in front of a blown-out window instead of being eaten by the halo, and characters keep their own skin tone instead of being tinted by whatever light is nearby (the glow adds a strongly warm cast — measured `R+6.93 G+4.66 B+2.04`).

## Attempt 5 — the colour, not just the light (FINAL)

**User feedback: "the saturated look of the original is gone".** Right again, and it follows from that warm cast: the glow was not only adding luminance, it was adding *chroma*. Gamma restores luminance and leaves colour flat.

Measured mean chroma (mean |channel − luma|):

| | luma | chroma |
|---|---|---|
| stock (glow on) | 70.05 | 6.459 |
| glow killed | 65.10 | 4.635 |
| glow killed + Gamma 54 | 70.87 | 4.695 |

ShadeBoost's saturation is `mix(luma, colour, slider/50)`, so the required slider is solvable directly — modelled offline over the captured frames, chroma reaches stock's 6.459 at **saturation ≈ 68**:

| saturation | 50 | 60 | 65 | **68** | 70 |
|---|---|---|---|---|---|
| chroma | 4.695 | 5.629 | 6.095 | **6.373** | 6.557 |

Confirmed live from the same savestate, patch loaded from file:

| | luma | chroma | black% |
|---|---|---|---|
| stock (glow on) | 70.05 | 6.459 | 8.84 |
| **final: glow off + Gamma 54 + Saturation 68** | **70.50** | **6.349** | **8.45** |

Brightness, colour and black level all land on stock, with none of the bleed. The important difference from stock is *where* the colour comes from: a tone curve has no spatial extent, so it saturates the character's own red costume instead of smearing a light's orange onto her skin.

Final per-game settings, `gamesettings/SLUS-20948_D31904C2.ini`:

```ini
[EmuCore/GS]
ShadeBoost = true
ShadeBoost_Brightness = 50
ShadeBoost_Contrast = 50
ShadeBoost_Saturation = 68
ShadeBoost_Gamma = 54

[Patches]
Enable = Remove Blur/Bloom
```

**Lesson: when you delete a screen-space effect, account for everything it contributed — luminance *and* chroma. Each user complaint here ("darker", "heavy glow", "less saturated") was a separate component of the same additive pass, and each was measurable before and after.**

This half of the fix is a **per-game emulator setting, not a pnach line**, so it ships as `gamesettings/SLUS-20948_D31904C2.ini`:

```ini
[EmuCore/GS]
ShadeBoost = true
ShadeBoost_Gamma = 54

[Patches]
Enable = Remove Blur/Bloom
```

(Or set it by hand: Game Properties → Graphics → Post-Processing → Shade Boost, Gamma 54.)

## Verification methodology (reusable)

PINE IPC (`EnablePINE = true`, TCP 28011) replaced the savestate-unzip loop from the Ys V devlog entirely:

1. Confirm serial + CRC of the *running* game before touching anything.
2. Hot-write candidate words mid-gameplay; the recompiler picks them up like a pnach write.
3. `PostMessage(WM_KEYDOWN, VK_F8)` to PCSX2's Qt windows takes in-app screenshots **without stealing focus** — usable while someone is playing.
4. Quantify instead of eyeballing: mean luminance for brightness, and `stock − effectkilled` differencing to isolate exactly what the effect contributes and *where it lands* (bucketed by scene brightness). Bucketing is what separated "haze on dark pixels" from "bloom on bright pixels" — a single mean would have called stock and zero-jitter identical.
5. Take several samples per variant: this glow's colour oscillates every frame, so single-shot comparisons are noisy (a static scene gave mean sd 0.01, so 4 samples was plenty).

## Deliberately left alone

- **`CBlurTask` radial blur**: dormant in all tested play — never constructed (`0x398D38` stayed NULL), and its ctor is reachable only through one indirectly-called function (`0x19EE18`). If it ever appears, the candidate kill is forcing the arbiter reads at `0x1AC07C`/`0x1AC12C` to zero.
- **Pass count `glow+0xA8`**: reducing it would tighten the bloom further at the cost of brightness. Not needed once the jitter is gone, and it is a runtime object field rather than static data.
- **PMODE soft filter**: display-level, same-buffer, one-line offset; PCSX2 anti-blur (default on) already cancels it.

## Final patch summary

`[Remove Blur/Bloom]` (recommended, default-enabled) — **pair it with the ShadeBoost settings above**:

| Patch | Purpose |
|---|---|
| `0032A200: 080CA954→03E00008` | `CGlowTask` draw thunk → `jr ra`: glow/bloom pass never dispatched |
| `0032A204: 8C840090→00000000` | former delay slot (`lw a0,0x90(a0)`) → `nop` |

`[Remove Blur/Bloom (keep bloom, fix ghosting only)]` (optional, mutually exclusive with the above) — for anyone who wants the bloom look and only the upscale ghosting gone; needs no ShadeBoost:

| Patch | Purpose |
|---|---|
| `0038BA44: 0000FFFF→00000000` | blur tap 1: `(-1,0)` → `(0,0)` |
| `0038BA48: 00000001→00000000` | blur tap 2: `(+1,0)` → `(0,0)` |
| `0038BA4C: 00010000→00000000` | blur tap 3: `(0,+1)` → `(0,0)` |

Both use `place=1` (every vsync). Not a `[No-Interlacing]` group, so no `gsinterlacemode` override.
