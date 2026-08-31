# Devlog: Remove Blur/Bloom for Crimson Tears (SLUS-20948)

How [`patches/SLUS-20948_D31904C2.pnach`](../patches/SLUS-20948_D31904C2.pnach) was made. Symptom: heavy haze and edge ghosting over the whole image, much worse at upscaled internal resolutions. PCSX2's GameDB already applies `halfPixelOffset: 4` + `nativeScaling: 4` ("Aligns/Fixes post effects") for this game and the ghosting survives them, so the fix had to remove the effect at the source.

Target: Capcom/DreamFactory brawler (2004), boot ELF `SLUS_209.48`, ELF CRC `D31904C2` (PCSX2 CRC = XOR of every little-endian u32 of the whole file — verified byte-identical against the record for this exact ISO in PCSX2's `cache/gamelist.cache`). The 2021 undub keeps the retail ELF, so the patch works for stock USA discs too. Tested on PCSX2 2.8.1, Vulkan, 3x scale. Single loadable segment maps `file_offset = va - 0x100000 + 0x80`; `$gp = 0x3A03F0`.

## Finding the effect (map of the ELF)

The binary keeps C++ RTTI names — `strings` alone gives the engine's class list (`drf::` = DreamFactory framework, `drf::ct::` = Crimson Tears game code). Two post-process systems exist:

| Address | What it is |
|---|---|
| `0x337520` | `CBlurTask` ctor — registers task `"BLUR"`, news a 0x90-byte radial-blur state (5 layers, decay weights 2.3/0.9/0.3/0.15/0.5, color 0x80808080), pointer kept at `gp-0x76B8` = `0x398D38` |
| `0x1AC078/0x1AC128` | scene-renderer arbiter: when `blur->enabled`, starts a named render layer at priority 0x14A, else stops it (event blur — dashes/skills set the flag at 4 sites) |
| `0x32A280` | `CGlowTask` ctor — registers task `"GLOW"`, vtable `0x398020` |
| `0x329E70` | `CGlowTask::update` — ping-pong lerps two RGBA sets (~±0.1/frame oscillation) into the glow color; gated on `task+0xA8` |
| `0x32A200` | `CGlowTask` draw thunk: `j 0x32A550 ; lw a0,0x90(a0)` |
| `0x32A550` | `CGlow::draw` — computes a **half-res buffer** (w/2 × h/2), allocs GS VRAM pages, builds a 0x200-qword GIF packet buffer: downsample → blend back over the frame. The feedback resample is exactly what ghosts under upscaling |
| `0x1668B8` | display putter — also runs a PMODE dual-circuit soft filter (ALP=0x80, both circuits on the same FBP, DISPLAY1 shifted one line). PCSX2's default anti-blur already neutralizes this, so it is not the culprit |

Route to the code: find the RTTI/tag strings (`"GLOW"`, `"BLUR"`, `drf::ct::CGlowTask`), locate their typeinfo records via aligned-pointer scans, then find the constructor as the code that materializes the tag string / vtable address via `lui`+`addiu` pairs. A full `lui 0x1200` sweep (every GS privileged-register store) ruled out display-level causes first.

## Choosing the patch point

`CGlow::draw` at `0x32A550` has exactly **one** entry in the whole image: the vtable thunk at `0x32A200` (no `jal` callers, no other `j`, the only data xref is vtable slot `0x398034`). Overwriting the thunk with `jr ra ; nop` severs the entire glow pass — no downsample, no blend-back — while `CGlowTask` itself keeps updating its color harmlessly and every other consumer of the task tree is untouched.

## Live verification with PINE (no savestate round-trips)

New tool for this repo's workflow: PCSX2's PINE IPC (`EnablePINE = true` in PCSX2.ini, TCP `localhost:28011`, tiny binary protocol — read8/32/64, write32, savestate, game ID). This session it replaced the savestate-unzip loop from the Ys V devlog entirely:

1. Confirmed serial + CRC of the *running* game via MsgID before touching anything.
2. Watched the globals live: glow one-time-init byte (`gp-0x77B8` = `0x398C38`) flips to 1 in menus and in-game → glow pass active exactly where the haze is seen.
3. Verified the original words at `0x32A200/0x32A204` were `080CA954 / 8C840090` (matching the static disassembly), then hot-wrote `03E00008 / 00000000` mid-gameplay.
4. Bloom vanished the same frame. In-app F8 screenshots before/after at the same spot: blown-out white railings became clean thin tubes, hot orange skin glow gone, floor texture and HUD visibly sharper. The EE recompiler picks up the write like any pnach write.
5. Game ran on stably (20k+ frames) with the patch resident.

Screenshot trick: F8 needs window focus via SendKeys/keybd_event, but `PostMessage(WM_KEYDOWN/UP, VK_F8)` straight to PCSX2's Qt windows takes in-app screenshots **without stealing focus** — usable while someone is playing.

## Deliberately left alone

- **`CBlurTask` radial blur**: dormant in all tested play — the object was never even constructed (`0x398D38` stayed NULL through boot → menus → in-game), and its ctor is only reachable through one indirectly-called function (`0x19EE18`, no static callers). If it ever shows up, the candidate kill is forcing the arbiter reads at `0x1AC07C`/`0x1AC12C` to zero (`lbu v0,($v0)` → `li v0,0`). Untested → not shipped.
- **PMODE soft filter**: display-level, same-buffer, one-line offset; PCSX2 anti-blur (default on) already cancels it. A `0x16697C` `ori 0x8023 → 0xFF23` (ALP=255) would kill it for software-renderer purists, but there was nothing observable to fix in HW.
- Character flicker seen during the intro/attract sequence: separate report, deprioritized this session. Worth rechecking with the glow patch active — the glow color oscillates every frame and bright characters were the most affected surfaces.

## Final patch summary

| Patch | Purpose |
|---|---|
| `0032A200: 080CA954→03E00008` | `CGlowTask` draw thunk → `jr ra`: glow/bloom pass never dispatched |
| `0032A204: 8C840090→00000000` | former delay slot (`lw a0,0x90(a0)`) → `nop` |

Group `[Remove Blur/Bloom]`, `place=1` (every vsync) like the rest of the repo. Not a `[No-Interlacing]` group, so no `gsinterlacemode` override.
