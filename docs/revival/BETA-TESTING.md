# OpenTTD 3DS Revival — r3r beta playtest

Selected 7 November2026. Original 3DS/3DS XL is the primary target; record any
New3DS results separately. Major features are playable, with an initial user
crash-free report. Extended stability, all menu combinations and audio quality
are still being tested. Networking and healthy AI support are not promised.
No safe maximum map size is certified; 256x256 is a useful test case, not a guarantee.

## Install and identify

Start from a working r3 installation with its graphics, language files, OpenSFX
bank and optional WAV soundtrack. Back up your executable and saves. Replace
only /3ds/openttd-revival-r3/openttd-revival-r3.3dsx. Keep data/gm/lang folders.
The small beta update does not contain those assets. Use disposable save copies.
For a fresh installation, obtain compatible base assets separately; do not assume
this executable-only package is a complete installation. Do not redistribute
private/commercial soundtrack or original TTD assets with reports.

Beta tag: revival-r3r-beta. Executable SHA256:
b99a2027f3c1381986b7fb2507c8ec48dbab2f13c02357d46a702478cd7e2112.
Keep the exact executable when reporting a crash. Developer symbols are retained
in the matching builds/repair-r3r/openttd.elf; another build's symbols won't do.

## Suggested sessions

- Start a new256x256 world and load an established copied game. Play normally,
  scroll/zoom, build and demolish; record session duration and in-game dates.
- Let monthly autosave run; manually save, exit, reload and continue.
- Buy trains and several wagons, check counts and long-consist scrolling. Pin
  depot above/shop below; test pointer mode, wagon dragging, station orders,
  closing windows and returning to map control. Try road/ship/aircraft menus.
- Exercise lower/upper menus and scrollbars, New Game/scenario editor and load UI.
- Try music autoplay, Next/Stop/volume and effects with and without music while
  building, loading and saving. Note dropouts, balance or missing effects.
- Check normal exit and suspend/resume. Note device model, launcher/CFW, SD card,
  map dimensions, town/industry density, vehicle counts and AI state.

## Report failures usefully

Include build/tag (or executable hash), device model, session length, exact action,
map size/date and whether audio was playing. State expected versus observed result
and whether it repeats. Attach a screenshot/video if useful. For a Luma crash,
retain the newest /luma/dumps/arm11/*.dmp plus boot.log, wav-music.log and
sound-effects.log from the game folder. Supply a copied save only if comfortable;
keep personal evidence out of the public source repository. No working save is
required for the initial ordinary-play case if the crash preceded first save.

For coding review, compare against upstream-v1.0.1 or the previous revival tag;
focus the graphics repair on environment/patches/SDL-1.2.15-render-lock.patch.
The source archive includes the full SDL source/build recipe and notices.
