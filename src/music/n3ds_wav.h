/* GPL v2. The SDL sound callback is the only audio output owner. */
#ifndef N3DS_WAV_H
#define N3DS_WAV_H
#ifdef N3DS
extern unsigned _n3ds_wav_output_rate;
void N3DSStopWavMusic();
void N3DSMixWav(void *buffer,unsigned frames);
#endif
#endif
