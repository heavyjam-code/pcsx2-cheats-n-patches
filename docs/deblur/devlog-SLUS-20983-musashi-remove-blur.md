# Devlog: Remove Blur for Musashi - Samurai Legend (SLUS-20983)

How [`patches/SLUS-20983_675CEB8F.pnach`](../../patches/SLUS-20983_675CEB8F.pnach) was made. Symptom: soft blur and ghosting around characters, much worse at raised internal resolution (reported at 4x, Vulkan).

Target: Square Enix action-RPG (2005), boot ELF `SLUS_209.83`, ELF CRC `675CEB8F`. Unlike the previous entries in this repo the CRC needed no cross-check against `gamelist.cache` — PCSX2 already ships a widescreen patch named exactly `SLUS-20983_675CEB8F.pnach` inside `resources/patches.zip`, which confirms serial and CRC outright. (The XOR-of-every-LE-u32 method was still re-validated against Crimson Tears' known `D31904C2` first.) Single loadable segment maps `file_offset = va - 0x100000 + 0x1000`; `.text` `0x100000..0x2d8b68`, `.data` `0x2d8b80`, `.rodata` `0x3aba00`.

PCSX2's GameDB entry for this serial is bare — `name`, `region`, `compat: 5`, and **no `gsHWFixes` at all**. No `halfPixelOffset`, no `nativeScaling`. Nothing at the emulator level compensates for this game's post-processing, which is why the artifact is so visible upscaled.

## The unlock: a full symbol table in `.sndata`

The ELF has no `.symtab`, but it does have a 640KB `.sndata` section at `0x30ba00` beginning with the magic `SNR1` — the SN Systems ProDG symbol table, left in the retail build. Layout:

| Offset | Meaning |
|---|---|
| `0x00` | `"SNR1"` |
| `0x0c` | VA of the symbol record array (`0x36128c`) |
| `0x10` | record count (`0x2f41` = 12097) |
| `0x35..` | packed NUL-terminated name strings |

Each record is 12 bytes: `{u32 name_va, u32 addr, u32 misc}`. Parsing it yields **12,097 named functions and globals**, GNU v2 (gcc 2.9x) mangled — `foo__5CBarif` = `CBar::foo(int,float)`, `_vt$5CBar` = vtable, `__5CBar` = ctor, `_5CBar$m_x` = static member. Every address matched EE RAM byte-for-byte over PINE, so RAM addresses equal ELF VAs directly.

This turned the usual blind hunt (string → typeinfo → vtable → ctor, as in the Crimson Tears devlog) into ordinary code reading. The engine is Square's "BF2" — Brave Fencer 2 — with source paths like `C__BF2_SYSTEM_MemMan.cpp` also left in.

## Finding the effect

`sym "blur|bloom|glow|focus"` over the symbol table returns the whole post-process surface immediately:

| Address | What it is |
|---|---|
| `0x00244a80` | `CDeFocus::CDeFocus` — singleton, pointer at `0x2dd1d8` |
| `0x00244d10` | `CDeFocus::disp` — calls `CGPrim::disp` on one `CDeFocusPrim`, then dispatches two `CBlurPrim`s |
| `0x002454b0` | `CDeFocusPrim::_makePktDeFocus` — the defocus packet builder |
| `0x00245b30` | `CBlurPrim::_makePktBlur` — the radial/zoom smear builder |
| `0x002d6438` | `CDeFocusPrim::calcZ` — `jr ra ; move v0,zero` |
| `0x002d65a8` | `CBlurPrim::calcZ` — `jr ra ; move v0,zero` |

Two candidates that looked promising were killed on sight by reading one word of EE RAM: `CHeatHazeSingleton::main` (`0x2cb210`) and `CDisplayFixEff::main` (`0x2ccef0`) both begin `03e00008` — `jr ra`. Empty stubs.

Object layout came from the one-line accessors rather than guesswork. `CGPrim`-derived prims keep their vtable pointer at `+0x14` (GCC 2.x vtables are `{short delta, short index, void* fn}` triples, which is why `CDeFocus::disp` does `lh a0,8(v0)` before `addu a0,s0,a0`). Relative to a `CBlurPrim` base: `+0x20` kind, `+0x24` rate, `+0x28` distance, `+0x2c` color, `+0x30` alpha mode. `getBlur__8CDeFocus` returning `this+0x90+i*0x38` confirmed the two blur prims sit at `+0x90` and `+0xc8`, and `getDeFocus__8CDeFocus` put the defocus prim at `+0x50`.

Live state told the rest of the story. During ordinary gameplay:

- both `CBlurPrim`s idle — `kind=0`, and `getPacketSize` returns 0 for kind 0, so they emit nothing
- `CDeFocusPrim` **running** — `flags=0`, near `30.0`, far `200.0`

During an in-game cutscene the second blur prim flips to `kind=1, rate=4, color=0x0a808080`. So there are two distinct effects, not one: an always-on defocus, and a scene-triggered radial smear.

Neither is a framebuffer feedback pass. Both builders read the camera at `*(0x2e94f8)+0x260` and run `SubVectorXYZ` / `Normalize` / `ScaleVectorXYZ` / `PointToPointDistance`, then emit layered translucent copies offset along a camera-relative direction. At native resolution those offsets are sub-pixel and read as softness; at 4x they separate into distinct ghost edges. The giveaway that the defocus pass is not a true depth-of-field is that **it softens the 2D HUD too**.

## Choosing the patch point

`CGPrim::disp` (`0x0010ac58`) is the gate:

```
lw   v1, 0x14(s0)      ; vtable
lh   a0, 0x28(v1)      ; delta for calcZ
lw   v0, 0x2c(v1)      ; calcZ
jalr v0
lui  v0, 0xf000
beql a1, v0, skip      ; calcZ == 0xF0000000 -> never added to the display list
jal  add2DispList
```

So returning `0xF0000000` from `calcZ` is the engine's own "do not draw" path — no packet built, no display-list entry, nothing else touched. Both `calcZ`s are two-instruction leaf stubs, so overwriting the delay slot `move v0,zero` with `lui v0,0xF000` is a **single word each**. Both sign-extend identically to `0xFFFFFFFFF0000000`, which is what the `beql` compares against on the R5900.

Uniqueness checked before committing to it: neither function has any `jal`/`j` caller, and each has exactly one data reference — its own vtable slot (`_vt$12CDeFocusPrim+0x2c`, `_vt$9CBlurPrim+0x2c`). The second "reference" a naive scan reports at `0x37ee40`/`0x37ee70` is the SNR1 symbol table's own address field, not code.

Alternatives considered and rejected: severing `CDeFocus::disp` (kills both effects with no separate toggle); forcing `getPacketSize` to 0 (the packet is skipped earlier than that, so it is the wrong lever); writing the prim flags directly (they live in heap memory at an address that changes between scenes — `0x01782e10` in one, `0x01504780` in another — so a pnach cannot target them).

## Live verification with PINE

Same setup as the Crimson Tears session: `EnablePINE = true`, TCP `localhost:28011`, and `PostMessage(WM_KEYDOWN/UP, VK_F8)` to PCSX2's Qt windows for in-app screenshots without stealing focus. Input works the same way — `PostMessage` of the mapped pad keys drives menus and cutscene skips without focus.

Measured from a static camera, stock vs patched, via edge-energy variance:

| Region | Stock | Patched | Change |
|---|---|---|---|
| Far background (trees) | 29.2 | 38.1 | **+30.5%** |
| HUD gears (top-left) | 96.4 | 110.1 | **+14.2%** |
| Near ground (bottom-left) | 82.6 | 81.6 | −1.2% |
| Whole frame | 89.7 | 93.1 | +3.7% |

Exactly the signature of a distance-based blur: distant geometry gains the most, ground right under the camera (inside the near plane of 30.0) is unaffected — and the HUD, which should never have been touched, gains 14%. Soaked 35 samples with the patch resident: no word drift, no PINE errors, no instability.

## Does it need brightness/saturation compensation? (No — measured)

The Crimson Tears patch in this repo needed a companion ShadeBoost curve, because the effect it removes
(`CGlow`) is an *additive* pass: deleting it cost 7.6% luminance and 28% chroma. That correction is
**not** transferable, and this game was measured rather than assumed.

Same-scene A/B via PINE, toggling `calcZ` between `move v0,zero` and the `0xF0000000` sentinel, three
samples averaged per variant:

| variant | luma | chroma | sharpness |
|---|---|---|---|
| stock | 69.99 | 15.622 | 4.974 |
| defocus off (`[Remove Blur]`) | 69.62 (**−0.5%**) | 15.550 (**−0.5%**) | +2.1% |
| both off (+ `[No Motion Blur]`) | 69.39 (−0.9%) | 15.560 (−0.4%) | +2.5% |

**Verdict: no ShadeBoost compensation for this game.** A defocus pass *redistributes* light — it averages
neighbouring pixels — where a glow *adds* it, so removing the blur returns the same photons to sharper
positions instead of deleting them. Adding Gamma 54 / Saturation 68 here would simply over-brighten and
over-saturate the game.

The patch is doing real work regardless — the effect is confirmed active, and it is confirmed to be
distance-keyed as `near=30/far=200` implies. Differencing stock against defocus-off, 32.5% of the frame
moves by more than 2 levels, and the change is concentrated in the distance:

| frame band | rows | mean |Δ| | pixels changed >2 |
|---|---|---|---|
| top (far geometry) | 0–543 | 5.93 | 42.4% |
| middle | 543–1086 | 3.45 | 47.7% |
| bottom (near ground) | 1086–1630 | 1.01 | 7.4% |

In the most-affected window, edge detail goes up 1.06x, and visually the difference is much larger than
that number suggests: a glowing orb loses a large smeared halo and becomes a crisp sphere, blue haze
stops washing over the rock face behind it, and background colour detail that the blur had flattened
(a magenta streak) becomes visible again. Global sharpness metrics understate a localised effect —
always difference the frames and look at where the change actually lands.

## Gotchas worth remembering

- **Pnach files only load at game boot.** A file dropped into `patches/` while the game is running does nothing, and the "patch doesn't work" report that follows is about an unpatched session, not a bad patch. Verify with a live read of the target word before diagnosing anything else.
- **A loose `.pnach` does *not* shadow the bundled `patches.zip` entry** — PCSX2 loads both and merges them, de-duplicating by group name (`Skipped loading patch 'Widescreen 16:9' since a patch with a duplicate name was already loaded`). I initially assumed the opposite and copied the bundled `[Widescreen 16:9]` group into our file defensively; the log proved that unnecessary and it was removed. Reuse a bundled group name only if you actually mean to shadow it.
- **Scoop's pcsx2 manifest does not persist `patches` or `gamesettings`**, so a scoop update wipes both. Fixing it at the manifest level is fragile (bucket edits get clobbered by `git pull`). The durable fix is PCSX2's own `[Folders]` section, since scoop *does* persist `inis`: set `Patches = ..\..\..\persist\pcsx2\patches` and add `GameSettings = ..\..\..\persist\pcsx2\gamesettings`. PCSX2 2.8.1 honours the `GameSettings` key even though it does not write it by default, and preserves both across its own ini rewrite on exit. The relative path resolves the same for any future version directory.
- **`pkill` does not kill Windows processes from git bash.** A leftover background script kept a PINE connection open and every subsequent write timed out, which looked exactly like a hung emulator. `Stop-Process -Id` from PowerShell is the reliable form.

## Deliberately left alone

- **`CEffTrailerModel`** and the rest of the trailer/afterimage system: never established whether it contributes, since the two `calcZ` patches were enough to satisfy the reported symptom in both gameplay and cutscenes. If character-edge ghosting ever shows up with these enabled, that is the next place to look.
- **`CLensEffect`, `CSunOcclPrim`, `CEffScreenMask`, `CShadow`**: not investigated. None of them were needed.
- **`[No Motion Blur]` is shipped disabled-by-default in spirit** — it is a separate group because the cutscene radial smear is a deliberate artistic effect, not a bug. It ghosts badly at 4x, so it is offered, but removing it changes the intended look.

## Final patch summary

| Patch | Purpose |
|---|---|
| `002D643C: 0000102D→3C02F000` | `CDeFocusPrim::calcZ` returns `0xF0000000` → the always-on defocus pass is never drawn |
| `002D65AC: 0000102D→3C02F000` | `CBlurPrim::calcZ` returns `0xF0000000` → the cutscene radial smear is never drawn |

Groups `[Remove Blur]` and `[No Motion Blur]`, both `place=1` (every vsync) like the rest of the repo. PCSX2's bundled `[Widescreen 16:9]` group for this CRC keeps working alongside them untouched.
