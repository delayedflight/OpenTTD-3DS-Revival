# r3r graphics repair — validation and baseline status

7 November 2026. Candidate for original 3DS/3DS XL, engine0.7.0.
Executable SHA256: b99a2027f3c1381986b7fb2507c8ec48dbab2f13c02357d46a702478cd7e2112.
Exact ELF and repaired libSDL hash retained in builds/repair-r3r/.
Branch fix/graphics-queue-baseline; changes are uncommitted, based on96348c8.
The complete supplied source snapshot, not HEAD alone, identifies this build.

## Repair

Dump00000008 (r3p, ordinary play before saving) matches the preserved r3p code
region. The immediate failure is libctru's gxCmdQueueClear panic: active queue
still running. SDK SDL1.2.15-19 uploads/sets texture state on the caller thread
while a private thread uses the same Citro3D state to begin/draw/end frames.

The separate LGPL SDL repair patch adds one static libctru LightLock covering
both paths. GPU-right checks occur inside it; every early exit releases it.
Upload releases before signalling the renderer. Existing GPU completion waits,
frame timing, software surfaces, worker shutdown and panic checks remain.
No additional screen/audio buffer or per-frame allocation is added. CPU threads
are serialized around graphics operations; existing GPU waits handle completion.
No gameplay/train-workshop or audio algorithm changes were made. One startup
log line identifies r3r. Removing a panic, adding a sleep, shrinking maps and
locking only the application's SDL_UpdateRect were not used as correctness fixes.

## Tests actually completed

- Actual SDK upload/render function bodies compiled in a controlled host model:
  forcing upload wait -> other-thread frame submit -> upload clear produces one
  old-code panic. The patched lock prevents that interleaving and produces zero.
  ASan/UBSan and TSan pass. 10,000 sequential upload/render handoffs pass, as do
  unavailable GPU, rejected frame begin, empty buffer and idle shutdown checks.
  This is a modelled queue condition, not physical-GPU reproduction or a proof
  that every graphics race/driver failure has been eliminated.
- Official SDL1.2.15 tarball and exact devkitPro patch hashes checked before build.
  SDL rebuilt in the contained image; game compilation succeeds. Linked executable
  disassembly confirms Lock/Unlock around upload and private renderer paths.
  Existing mixed-enum ABI warnings remain. No bit-identical rebuild claim.
- Train-workspace actual-code sanitizer suite passes (including20 screen transfers),
  and paired-depot cached-scroll oracle passes30/30. All generated language files
  are checked against r3q before packaging; existing language assets are retained.
- Azahar2126.2 arm64, original-3DS-mode disposable profile with copied established
  256x256 Flufingwell1980 game, WAV album and OpenSFX bank. Exact candidate boots,
  loads, runs, scrolls/zooms and switches normal/construction mode; two monthly autosaves
  complete; the observed game reached22 October1980. Recorded WAV underruns/I/O errors are zero and effects trigger.
  Touch-based menu checks remain blocked by desktop automation coordinate errors;
  no full r3r train-purchase walkthrough or audible-quality assessment is claimed.

## Original-console checkpoint still required

Use a disposable new256x256 game and an established copied save. Test ordinary
play/scrolling/zoom, menus and screen pins, repeated control transfers, train
purchase/wagon drag, music/effects, autosave/manual save/reload, then an extended
session. Record duration and exact action on any failure; retain new dump plus
boot/audio logs. Verify suspend/resume and normal exit. Compare responsiveness
with r3q if safe; do not claim a performance gain without measurements.

This is a repaired baseline candidate. It becomes a verified hardware baseline
only after those tests. No heap headroom, safe map size or universal crash fix is
established. The exact user-crash timing/interleaving remains inferred from dump,
SDK source and modelled reproduction, not captured on the original hardware.
No device or protected save was written, and no Git commit/tag/push was made.

Sources: original SDK patch at devkitPro/pacman-packages/3ds/SDL; libctru2.7.0
source/gpu/gxqueue.c and Citro3D1.7.1 source/renderqueue.c. See CRASH-00000008.md.
Reproduce host test: python3 docs/revival/tests/graphics-queue.py /tmp/ottd-gx.
Rebuild/relink: bash environment/build.command. Official SDL source, notices,
original platform patch, separate repair patch and build scripts are included.

## Beta acceptance — 7 November2026

After this build was delivered, the user reported no crash so far and approved
committing it as the beta for other playtesters because the major features work.
No duration or complete hardware checklist result was supplied. r3r is selected
as the playable beta baseline; longer tests and reliable crash reports remain
necessary. The executable is unchanged. Source is committed under
revival-r3r-beta after this acceptance; earlier references to an uncommitted
candidate describe its build-time state. No device write or remote push occurred.
