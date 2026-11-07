# Architecture and optimisation boundaries

Source review: 7 November 2026. This is a map of the current implementation;
[STATUS.md](STATUS.md) owns progress and [BENCHMARKS.md](BENCHMARKS.md) owns results.

## Engine and platform boundary

OpenTTD 0.7.0 remains the simulation/save engine. `src/openttd.cpp` coordinates
startup/game loop; `src/map.cpp` allocates contiguous Tile and TileExtended arrays
for every map tile. Vehicles, cargo, stations and companies remain engine-managed
objects/pools. Simulation is world-wide, including vehicles outside the viewport.
There is no view-distance unloading, virtual-memory SD cache or compressed live map.
Map allocation is only one component of memory; object pools, sprite caches,
rendering, audio and transient load/save allocations also need accounting.

N3DS code is selected in `config.lib`; it uses ARMv6K/libctru and 3ds-sdl.
`environment/build.sh` disables networking, zlib, PNG, Unicode/font dependencies
and the generic thread backend. It retains GNU++11 and compatibility workarounds,
including -fno-lifetime-dse and several disabled optimisations. Their performance
cost is unmeasured; removing them may reintroduce earlier correctness faults.

## Rendering, UI and input

| Source | Responsibility |
|---|---|
| `src/video/sdl_v.cpp` | SDL dual-screen output, separate UI software surface, lower-panel composition, native-row presentation, physical input and screen modes |
| `src/window.cpp`, `src/window_gui.h`, `src/n3ds_ui.h` | Window layout, per-window state, ownership, hit testing, pinning and bounded dragging |
| `src/viewport.cpp` | Cached viewport scrolling/clipping; must respect windows on the same drawing surface |
| `src/n3ds_controls.h` | Shared construction click/hold state |
| `src/n3ds_menu_scroll.h` | Bounded large-window workspace scrolling |
| `src/*_gui.cpp` | Class-specific native forms and layout; depot/build_vehicle handle train pairing/counts |

The logical drawing width is 400, height 240. SDL creates dual-screen software
output with double height plus a separate UI layer of 240 rows matching its pitch.
The 320x240 touchscreen presents a native lower workspace; larger menus can use
scrollable workspaces or an optional upper-screen workspace. Layout and pixel/input
mapping must agree. There is no general font/icon scale setting that fixes every
legacy window. `N3DSTopWindow` is the shared authority for surface ownership,
hit testing, occlusion and cached-scroll protection.

Normal play displays the map above and menus below. X/Select changes construction
control mode; ordinary Circle Pad map scrolling and bumper zoom coexist with
construction click/hold controls. Upper UI uses pointer mode. Train-depot pinning
can place only the depot above while purchase remains below; X/Y/Select toggles
DEPOT CONTROL for the upper pointer. Focus transfer releases shared held state.
A paired depot reuses existing surfaces, rather than allocating another UI surface.

## Audio and lifecycle

- `src/music.cpp`, `src/music.h`, `src/settings.cpp`: loose WAV track names on
  N3DS and one-time valid-track autoplay initialisation, preserving later Stop.
- `src/music/n3ds_wav.cpp`: libctru reader worker, default application core,
  16,384-byte stack, 10 ms sleep between refill cycles; SDL-lock publication.
- `src/music/wav_stream.hpp`: bounded RIFF PCM reader/resampler/mixer with
  65,536-byte source ring. Supported source is PCM16 mono/stereo, 8–48 kHz.
- `src/sound/sdl_s.cpp`, `src/mixer.cpp`: shared SDL callback/effects mix; WAV
  requests 22,050 Hz output and uses actual device rate. Verify backend paths
  against source before changes; do not add disk access or logging in callback.
- `src/sound.cpp`: legacy CAT catalogue and per-effect reads; eight mixer channels
  reserve/publish under SDL audio lock while allocation/file I/O occur outside it.

Music streams each track; the entire album is never loaded. Shutdown disables
callback use, signals reader stop, joins/frees the thread and closes the stream
before output destruction. Large file size is not the live-ring budget.
The converted OpenSFX bank is read per effect, not preloaded as a whole. Numeric
sample bounds and tested conditions belong in BENCHMARKS, not a total-RAM claim.

## Stability and design decisions to preserve

N3DS pool-validity cleanup uses volatile writes in `src/company_cmd.cpp` and
`src/cargopacket.cpp`, with compiler lifetime workarounds in config.lib.
AI failure handling in `src/ai/ai_instance.cpp` logs stopped AI and suppresses
automatic debug-window opening. Suppression is not evidence of working AI.
`src/n3ds_bootlog.h`/startup logging support launch/crash diagnosis.

Known failed approaches: a game-loop-only music refill underruns during load;
use the bounded reader worker. Viewport scrolling that ignores surface ownership
corrupts separate UI/depot pixels; use shared ownership/clipping. Rescaling broad
legacy menus without matching hit geometry causes difficult or wrong selection.
Upstream title assets use compression absent from this build; revival uses a small
64x64 backdrop rather than assuming the bundled animated title will load.

Original 3DS/XL application-usable RAM is not the device's full advertised physical
RAM. No live heap headroom or SD throughput budget has been measured here.
Do not assume extra cores, New-3DS resources or spare CPU from emulator speed.
Preserve compatibility, save format, bounded audio and exact-symbol provenance.
Detailed algorithms/history: `docs/revival/IMPLEMENTATION.md`, `WAV-MUSIC.md` and
`OPENSFX-CONVERSION.txt`; read their relevant sections only.

## r3r graphics synchronization candidate

The contained toolchain now rebuilds SDL1.2.15 with the vendored official 3DS patch
and a separate environment/patches/SDL-1.2.15-render-lock.patch. A static LightLock
covers both upload/texture configuration and private-thread frame rendering.
Existing GPU queue waits and shutdown remain. The source/config generator tools
run only inside Docker. See GRAPHICS-QUEUE-VALIDATION.md for the controlled overlap
reproduction and limits; original-console validation remains pending.
