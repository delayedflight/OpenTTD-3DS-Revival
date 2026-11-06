# OpenTTD 3DS Revival — current handover

Updated 2026-11-07. Target: original Nintendo 3DS / 3DS XL, OpenTTD 0.7.0.

## Start here

The canonical Git repository is `OpenTTD 3DS Revival/source/`, branch
`revival/main`. Read this file, PROJECT-ORGANISATION.md and `git status` first.
Old `work/r*-source` directories are preserved historical evidence, not the
active checkout. Do not resume changes there. See RELEASES.json for 21 recovered
release commits/tags. All original upstream history is retained.

## Current release and evidence

r3q adds a native train depot, explicit engine/wagon counts, larger purchase
rows with scrollable details, and optional depot above / shopping below.
Pin depot/shop to toggle. X/Y/Select switches DEPOT CONTROL and shopping;
Circle Pad moves the upper pointer, A/L clicks/holds, D-pad up/down scrolls.
Small native windows retain bounded caption positions. No third framebuffer.
Read IMPLEMENTATION.md and TRAIN-WORKSPACE-VALIDATION.txt for exact scope.
Build SHA256: 79dc5eccc7852f55700a5a76d0837a69edc0f123884c10e244f73b1997fd2717.
Exact matching ELF is retained in project builds/repair-r3q/.

Docker compilation, 15 UI sanitizer/regression suites and 30 depot/20 original
cached-scroll cases pass. Development emulator verified buying one MJS250 plus
one Copper Ore Hopper, with 1 engine / 1 wagon shown. Final exact executable
loads the disposable Flufingwell fixture, opens depot and simulates/autosaves.
Final touch-based purchase repetition was blocked by desktop automation's
windowNotFoundAtPosition errors; keyboard/screenshot actions worked. Hardware
train workshop checks remain. Existing mixed-enum linker warnings remain.

Earlier changes: original AI crash repair (r1b); upper map/native lower menus,
pointer/construction controls, cached-scroll fixes and menu scaling; editor and
New Game pages (r3m); bounded threaded WAV streaming (r3n); autoplay and all22
tracks (r3o); compatible OpenSFX effects + mixer publication locking (r3p).
Music uses a 64 KiB ring and 16 KiB worker stack, with SD I/O outside the audio
callback. Do not preload the soundtrack. No engine upgrade, networking or
healthy AI support is claimed. User has two beta testers, one a developer.

## Current blocking evidence to obtain — no crash diagnosis started

User reports a Luma crash on original 3DS XL using a 256x256 map.
Build, trigger, save and new dump are not known. SD was not mounted at last
check. Obtain newest ARM11 .dmp plus exact executable/build and affected save.
Do not assume memory exhaustion from a Luma exception or certify a safe map
size. Original author generated 1024x1024 on O3DS, but that is not long-session
stability evidence. Our emulator results also do not establish hardware limits.
User paused diagnosis to organise Git and outputs; finish organisation first.

## Safety and workflow

Never write to the user's SD/device or original saves. Preserve protected
copies in project work/recovered-save/original and work/crash-dumps. Use new
disposable copies in emulator profiles. Do not publish saves/dumps/private
soundtrack. Preserve each release binary and matching ELF. Install executable
updates by replacing only the .3dsx; the user previously accidentally replaced
the whole data folder and lost graphics files.

Future work happens on small feature/fix branches from revival/main, with
meaningful commits. Update this handover, implementation notes, validation and
release index at milestones. Prefer narrow source searches and relevant tests;
read only the sections needed instead of replaying all prior chat history.
Keep uncertainty explicit. Do not create/push a GitHub fork without instruction.

## Useful paths (relative to overarching project)

- source/: canonical code, tests, documentation, contained build recipe.
- outputs/latest/: r3q release links; outputs/README.md is the browsable index.
- outputs/releases/<release>/: packages, source, notes, screenshots, logs.
- outputs/organisation/: recovery guide, output-move hashes, Git backup bundle.
- builds/repair-r3q/: exact tested executable and debug symbols.
- logs/: original build/test logs; work/tests/: disposable emulator profiles.
- work/emulator/azahar-macos-arm64-2126.2/: Azahar 2126.2; user symlink selects
  the disposable profile. Latest train profile: work/tests/repair-r3q-train-ui.

Build: start Docker Desktop, then run `bash environment/build.command` from
project root; it now selects source/. Alternatively run the same command from
the source repository; its outputs then stay in source/builds and source/logs.
The pinned toolchain recipe and existing configure flags are unchanged.
