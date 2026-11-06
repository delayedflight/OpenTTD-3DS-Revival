/* $Id$ */

/** @file sdl_s.cpp Playing sound via SDL. */

#ifdef WITH_SDL

#include "../stdafx.h"

#include "../mixer.h"
#include "../sdl.h"
#include "sdl_s.h"
#include <SDL.h>
#include "../music/n3ds_wav.h"

static FSoundDriver_SDL iFSoundDriver_SDL;

static void CDECL fill_sound_buffer(void *userdata, Uint8 *stream, int len)
{
	MxMixSamples(stream, len / 4);
#ifdef N3DS
 N3DSMixWav(stream,len/4);
#endif
}

const char *SoundDriver_SDL::Start(const char * const *parm)
{
	SDL_AudioSpec spec;
 memset(&spec,0,sizeof(spec));

	const char *s = SdlOpen(SDL_INIT_AUDIO);
	if (s != NULL) return s;

	#ifdef N3DS
 spec.freq=GetDriverParamInt(parm,"hz",22050);
#else
 spec.freq = GetDriverParamInt(parm, "hz", 11025);
#endif
	spec.format = AUDIO_S16SYS;
	spec.channels = 2;
	spec.samples = 512;
	spec.callback = fill_sound_buffer;
	if(SDL_CALL SDL_OpenAudio(&spec,&spec)<0){SdlClose(SDL_INIT_AUDIO);return "SDL audio open failed";}
 if(spec.format!=AUDIO_S16SYS||spec.channels!=2||spec.freq<8000||spec.freq>48000){SDL_CALL SDL_CloseAudio();SdlClose(SDL_INIT_AUDIO);return "Unsupported SDL audio format";}
 MxInitialize(spec.freq);
#ifdef N3DS
 _n3ds_wav_output_rate=spec.freq;
#endif
	SDL_CALL SDL_PauseAudio(0);
	return NULL;
}

void SoundDriver_SDL::Stop()
{
#ifdef N3DS
 N3DSStopWavMusic(); // Join the reader before SDL destroys its audio lock.
#endif
	SDL_CALL SDL_CloseAudio();
#ifdef N3DS
 _n3ds_wav_output_rate=0;
#endif
	SdlClose(SDL_INIT_AUDIO);
}

#endif /* WITH_SDL */
