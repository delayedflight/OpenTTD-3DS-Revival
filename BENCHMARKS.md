# Measurements and repeatable testing

Evidence inventory: 7 November 2026. r3r correctness verification is recorded below; it is not a hardware performance baseline. Functional checks below are not hardware performance baselines.

## Recorded results and conditions

| Evidence | Recorded result | What it does not establish |
|---|---|---|
| r3q host UI harnesses, clang++ sanitizers | 15 suites pass; depot cached-scroll 30/30, original split-scroll 20/20 | End-to-end hardware controls, FPS or RAM |
| r3o host reader, all 22 supplied tracks, ASan/UBSan | 103,633,824 output frames at 22,050 Hz; no recorded underruns/I/O errors; TSan lifecycle tests pass | Original SD latency or audible quality |
| r3o/r3p Azahar 2126.2 arm64, copied Flufingwell, music load/autosave/effects | Zero recorded underruns/I/O errors in reported sessions | Whole-album or long-session hardware stability |
| r3p host CAT/mixer, ASan/UBSan and TSan | 71 nonempty sounds produce output; 3,000 concurrent trigger exercise passes | Speaker quality, peak process RAM or console timing |
| Early music prototype, emulator save load | Game-loop-only refill recorded 479 underrun callbacks; worker replaced it | A general throughput benchmark |
| Original public build, original-3DS-mode emulator, empty worlds | 256x256 generation/save/reload and 1024x1024 generation/first autosave pass; short 2048x2048 attempt inconclusive | Safe map sizes, late-game density or physical-hardware capacity |
| User report + dump00000008, original 3DS XL, r3p, 256x256 | Ordinary-play crash; matched ELF identifies graphics-queue panic | Root cause/interleaving, RAM exhaustion or safe map limit |

Evidence files: `docs/revival/{TRAIN-WORKSPACE-VALIDATION.txt,WAV-VALIDATION-r3o.txt,
SOUND-EFFECTS-VALIDATION.txt}`. Parent `outputs/reports/Preliminary test report.md`
records old empty-world tests. Parent `logs/` retains exact build/test logs.

Source-derived bounds, **not measured total memory**: music ring 65,536 bytes +
16,384-byte reader stack, plus thread/stdio/SDL/allocator overhead. Converted bank
has 73 slots, 71 nonempty; largest PCM sample 44,654 bytes; eight such active samples
would hold 357,232 bytes plus metadata. Bank-on-SD size is 1,661,236 bytes.

## Build and environment to record

r3q: devkitARM r68-1, libctru 2.7.0-1, 3ds-sdl 1.2.15-19; exact inventory in parent
`builds/repair-r3q/toolchain-packages.txt`. Digest and configure flags live in
`environment/`. Keep executable SHA, matching ELF, source commit/tag, inventory,
compiler flags and source diff for every measured build. Historical results may
refer to earlier releases, not necessarily r3q. r3r has been built from the uncommitted repair snapshot with rebuilt SDL; no
controlled hardware benchmark has been performed. Package resolution is not
fully frozen by pinning the base image alone. Mixed-enum ABI warnings remain.

## Baselines still required — no values assumed

No controlled original-3DS FPS, simulation throughput, peak/free heap, fragmentation,
CPU utilisation, SD throughput/latency, load/save duration or long-run leak slope
is available. Candidate investigation areas are world/pool growth, load/save peaks,
render/redraw costs, compiler workarounds and SD/audio contention; none is a ranked,
confirmed performance bottleneck. Treat the new 256x256 crash as separate evidence.

## Proposed controlled hardware procedure

1. Record original versus New 3DS/XL, launcher/CFW, SD model/filesystem/free space,
   exact binary/ELF and configuration, graphics/effect bank, music track and save SHA.
2. Use disposable copies of fixed saves/seeds, including established Flufingwell
   and sparse/dense 128x128 and 256x256 worlds. Hold date, view, zoom, vehicles,
   town/industry density and AI state constant; only one variable changes per run.
3. Separately time cold load, five minutes fixed-view simulation, a prescribed
   scrolling/building sequence, monthly autosave and manual save/reload. Define
   the observation interval and repeat at least three times, reporting every run.
4. Repeat audio off, music only, effects only and both under otherwise identical
   conditions. Collect wav-music.log underrun/I/O counters and boot/effects logs.
5. Add heap/timing instrumentation in a separately authorised code task; sample
   at controlled points, including load/save boundaries. Record instrumentation
   overhead. Capture crashes/dumps plus immediately preceding action and timestamp.
6. Retain failures and raw logs, compare median/range, and distinguish emulator
   functional tests from physical-console performance. Long-session and multi-device
   checks are required before recommending limits. Never test original save files.

Results entry template: date; hardware/SD/launcher; source+binary+ELF identity;
config/save/seed; scenario/duration/repetitions; metric+units+raw values; errors;
log location; conclusion and remaining uncertainty. Add entries only after tests.

## Focused test commands (from repository root)

```sh
python3 docs/revival/tests/train-workspace.py /tmp/ottd-trains
python3 docs/revival/tests/check-depot-scroll.py ../work/r3p-source . /tmp/ottd-depot-scroll
python3 docs/revival/tests/check-split-scroll.py ../work/tests/repair-r3l-scroll/r3-source.cpp . /tmp/ottd-split-scroll
python3 docs/revival/tests/wav-stream.py /tmp/ottd-wav '/path/to/private/sample.wav'
python3 docs/revival/tests/sound-effects.py /tmp/ottd-effects ../work/opensfx-legacy/sample.cat
```

Python 3 and host clang++/sanitizer support are required. Private paths/old baselines
exist only in this development workspace; on a fresh clone obtain the corresponding
fixtures/assets separately. The other fourteen UI suite names are listed in the
train validation report and accept an output directory like the train test.
Do not rerun all tests for documentation edits; validate links and source claims.

## r3r correctness checkpoint

Actual SDK upload/render functions, controlled host queue model: old interleaving
panics once; patched lock excludes it (zero panics), 10,000 sequential handoffs
plus early exits/shutdown pass ASan/UBSan and TSan. Real library/game compilation
and linked-lock inspection pass. Azahar2126.2 with copied256x256 Flufingwell passes
scroll/zoom/control transfers and monthly autosave while music/effects run; no
recorded audio underruns/I/O errors. These are functional observations, not RAM/FPS
measurements or original-console reproduction. Details: docs/revival/GRAPHICS-QUEUE-VALIDATION.md.

### Initial user hardware feedback — 7 November2026

r3r: no crash observed so far; user considers major features working and approves
wider beta playtesting. Exact duration/map/actions/SD conditions were not recorded.
No numeric FPS/RAM/SD metric or complete regression result can be inferred.
