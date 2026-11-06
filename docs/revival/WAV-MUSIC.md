# r3n WAV streaming prototype

## Install the private sample update

Back up the current r3 executable. Extract the update into the SD root, merging folders. It supplies only:

- `3ds/openttd-revival-r3/openttd-revival-r3.3dsx`
- `3ds/openttd-revival-r3/gm/gm_tt00.wav` — the user's supplied theme sample, unchanged.

Keep existing data, languages, configuration and saves. This is an update for an existing r3 installation. No device or original save has been modified by development/testing.

Open a game, go to the second toolbar page, choose Sound/music and press Play in Jazz Jukebox. Select All tracks. Only the theme is installed, so it repeats. The music-volume slider is independent of effects volume. The theme can also play on the title screen if music was already enabled in the configuration.

If a configuration explicitly selects the null music driver, leave `musicdriver` blank or select `wav`; sound must be SDL (`sounddriver` blank or `sdl`). Do not replace your entire configuration with a test configuration. Unsupported/missing WAV files stop playback and are described in `wav-music.log` beside the executable.

## Format and filenames

The supplied file is 44,100 Hz, 16-bit signed PCM, stereo, 77.64 seconds, 13,695,740 bytes including its header. SHA256: `aa9f451e34384acdafbec71cc0cebe3b9851293ad5a0a1d5d35d06b35016f4a5`.

Accepted input: RIFF WAVE, ordinary PCM format tag 1, 16-bit mono or stereo, 8–48 kHz. Floating point, 24-bit, compressed WAV and WAVE extensible are rejected. Unknown metadata chunks and odd padding are skipped safely. Track files must be loose files in the `gm` directory; WAV files inside a tar are not supported.

`WAV track filenames.csv` maps song titles to the required filenames. Album numbering is different from the internal `gm_ttNN` numbering: the theme is `gm_tt00.wav`. Add other tracks only when their titles match. No other tracks were supplied for testing.

## Bounded playback

The sample is read through a fixed 65,536-byte source ring. The reader object is 65,608 bytes in the 64-bit host test; ARM layout can differ. One libctru worker has a 16 KiB stack plus thread/TLS/stdio overhead. SDL retains its existing output buffers. This is approximately 80 KiB of explicit ring/stack storage, not a measurement of the game's total RAM use.

The worker refills outside the SDL audio lock in at most 8 KiB reads, sleeps 10 ms between passes, and runs on the default application core. It needs no New 3DS-only CPU or extra core permissions. Metadata is committed with the SDL audio lock; unpublished ring space cannot be consumed. The SDL callback never reads from SD, allocates a track or logs. Stopping disables the callback, joins the reader and then closes the file. Audio shutdown joins the reader before SDL destroys its lock.

The prototype requests 22,050 Hz stereo output. The 44.1 kHz source is resampled while mixing; it is not played slower. Volume is scaled independently and mixed samples saturate to signed 16-bit limits. The effects mixer is initialized to the obtained SDL frequency, keeping effect pitch correct. Exact-rate/integer-step samples avoid unnecessary 64-bit interpolation divides. If reads do fall behind, music contributes silence until data arrives; effects remain in the output. The log records callback underrun events, not elapsed silence duration.

## Audio setup

SDL uses the 3DS DSP audio backend. On hardware it requires `/3ds/dspfirm.cdc`. The official devkitPro audio example explains how a user can obtain it through Luma's Rosalina menu, Miscellaneous options, Dump DSP firmware: https://github.com/devkitPro/3ds-examples/blob/master/audio/README.md

An empty firmware marker was used only in the disposable emulator profile, where audio is emulated. Do not copy an empty marker to hardware. Missing audio support falls back to the existing silent driver and is reported as `audio unavailable` in the music log.

## Validation and limits

See the accompanying validation report. The full sample, metadata/padding, five rates, mono/stereo, clipping, mute, EOF, short reads, buffer starvation, restart and malformed files are exercised by the actual-code host harness. The threaded driver test consumes more than its prefetched buffer without any game-loop polling, tests thread allocation failure, and joins twenty rapid restarts. Address/undefined-behaviour and thread sanitizers pass. The SDL callback/startup harness checks effects mixing, output-rate propagation, missing audio/open/format failures and stop order.

Reproduce with your own sample (audio is excluded from corresponding source):

```sh
python3 source/docs/revival/tests/wav-stream.py /tmp/openttd-wav /path/to/sample.wav
clang++ -std=c++11 -O1 -fsanitize=thread /tmp/openttd-wav/wav-stream.cpp -o /tmp/openttd-wav/wav-stream-tsan
cd /tmp/openttd-wav
./wav-stream-tsan /path/to/sample.wav
```

Original-console sound quality, CPU/RAM headroom, SD latency during autosaves and long play sessions still need hardware testing. Emulator progress counters verify that audio samples reached the callback; they are not an auditory quality assessment or proof of original-console performance. The pre-existing mixed-enum ABI linker warnings remain.
