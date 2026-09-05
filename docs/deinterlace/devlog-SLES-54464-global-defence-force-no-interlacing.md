# Devlog: No-Interlacing for Global Defence Force (SLES-54464)

Record of how the `[No-Interlacing]` group in
[`patches/SLES-54464_DD35AC9F.pnach`](../../patches/SLES-54464_DD35AC9F.pnach) was made. The
build, the display code and the video-mode words are described in
[the 60 FPS devlog](../60fps/devlog-SLES-54464-global-defence-force-60fps.md); this one only
adds the progressive switch.

Target: the PAL release of Earth Defense Force 2, ELF `SLES_544.64`, CRC `DD35AC9F`. PCSX2
bundles only a `[Widescreen 16:9]` group for it.

## The tier

The 2x internal-resolution capture of stock is 1280x896 - the vertical doubles - so the game
renders a full 640x448 frame and interlaces only on output: the one-to-three-word tier. The GS
dump confirms it from the other side: every scene draw uses one `XYOFFSET`
(`0x720000006C00`), no draw uses `SCANMSK`, and the two frame buffers (`FBP` 0 and `0x8C`)
alternate whole frames. Both buffers' display entries in the game's table read the same
`DISPLAY` (`DX` 640, `DY` 50, `DH` 447) and the same draw offsets, so there is no per-field
half-line bob to stand down either.

## The words

`sceGsResetGraph(0, 1, 3, 0)` at `0x0012C038` is the only display init. Its `inter` and
`ffmd` arguments become `SMODE2 = INT | FFMD << 1`, and the game's own display builder at
`0x0012ADD0` hardcodes `DISPLAY.DY`. Following the GitS SAC recipe:

| Patch | Purpose |
|---|---|
| `0012C030: 24050001 -> 24050000` | `inter` 0: `SMODE2.INT` off |
| `0012C03C: 0000382D -> 24070001` | `ffmd` 1: read every line (`SMODE2` = 2, libgraph's own non-interlaced value) |
| `0012C034: 24060003 -> 24060002` | `omode` NTSC - the same word the 60 FPS and NTSC Mode groups write |
| `0012B07C: 3C010006 -> 3C010001`, `0012B0B4: 34228000 -> 34229000` | `DISPLAY.DY` 25: it counts half-lines while `INT` is set and scanlines once it is clear, so the NTSC 50 halves |
| `0012B0C8: 64020290 -> 64020280` | `DISPLAY.DX` 640, the NTSC value, shared with the other two groups |

`DH` stays 447 and the buffers stay 640x448. The group also carries `gsinterlacemode=1`, so
PCSX2 stops deinterlacing while it is enabled. The video-mode words are the same as the 60 FPS
and NTSC Mode groups', and PCSX2 applies groups in file order, so this group sits last in the
file: its `DY` 25 wins over their 50 when both are ticked, and it is complete on its own when
they are not. Standalone it therefore implies NTSC output; a PAL progressive variant would need
`DY` 52 (the port centred its 448 lines at 104) and was not built.

## Verification

Fresh boot with `[60 FPS]`, `[Remove Blur]` and `[No-Interlacing]`: `sceGsGParam` reads
`inter` 0, `omode` 2, `ffmd` 1; the game's `DISPLAY1` reads `0x001BF9FF_01819280`, i.e. `DY` 25
with everything else as before; PCSX2 logs `Setting deinterlace mode to 1 by patch request`
and `Mode Changed to NTSC`; the title captures as a full 2560x1792 frame at 4x rather than the
1x1 an empty CRTC rectangle produces, and missions play and load normally. Loading a savestate
made under an interlaced boot brings that boot's GS registers back, as savestates do, but the
deinterlacer stays off through the group's key, so the picture is the same either way.

## What it did not do

It was tried as the cure for a "double stair-step" on distant buildings at 60 fps. It is not:
forcing the deinterlacer off changed nothing about that doubling, which was the game's
depth-of-field pass and is covered in
[the Remove Blur devlog](../deblur/devlog-SLES-54464-global-defence-force-remove-blur.md).
The group earns its place the usual way, by taking a deinterlacer out of a progressive frame's
path.
