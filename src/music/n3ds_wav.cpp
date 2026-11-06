/* GPL v2. Stream user-provided PCM WAV files; never load a whole track. */
#ifdef N3DS
#include "../stdafx.h"
#include "music_driver.hpp"
#include "n3ds_wav.h"
#include "wav_stream.hpp"
#include "../sound_func.h"
#include <SDL.h>
#include <3ds.h>

unsigned _n3ds_wav_output_rate=0;
static RevivalWavStream _wav;
static bool _reported_end=false;
static bool _wav_callback_enabled=false;
static uint64_t _next_report=0;
static Thread _wav_reader=NULL;
static bool _wav_reader_stop=true;

void N3DSMixWav(void *buffer,unsigned frames)
{
 if(_wav_callback_enabled)_wav.Mix(static_cast<int16_t *>(buffer),frames,_n3ds_wav_output_rate);
}
static void WavLog(const char *event)
{
 if(_n3ds_wav_output_rate!=0)SDL_LockAudio();
 unsigned rate=_wav.rate,channels=_wav.channels,peak=_wav.peak,underruns=_wav.underruns;
 unsigned long long frames=_wav.output_frames;bool io_error=_wav.io_error;
 if(_n3ds_wav_output_rate!=0)SDL_UnlockAudio();
 FILE *log=fopen("wav-music.log","a");if(log==NULL)return;
 fprintf(log,"%s rate=%u channels=%u ring=%u peak=%u output_frames=%llu underruns=%u io_error=%d output_rate=%u\n",event,rate,channels,RevivalWavStream::CAPACITY,peak,frames,underruns,io_error,_n3ds_wav_output_rate);
 fclose(log);
}
static void PumpWav()
{
 for(unsigned budget=RevivalWavStream::CAPACITY;budget!=0;){
  SDL_LockAudio();unsigned n=std::min(_wav.FreeWriteBytes(),std::min(budget,8192u));SDL_UnlockAudio();
  if(n==0)break;
  unsigned got=_wav.ReadFile(n); // Disk I/O never runs in the callback or with its lock held.
  SDL_LockAudio();_wav.Publish(got,n);SDL_UnlockAudio();
  budget-=n;if(got!=n)break;
 }
}
/** Same default application core on old/new 3DS; no extra core permission. */
static void WavReader(void *)
{
 for(;;){
  SDL_LockAudio();bool stop=_wav_reader_stop||_wav.eof;SDL_UnlockAudio();
  if(stop)return;
  PumpWav();svcSleepThread(10000000LL);
 }
}
void N3DSStopWavMusic()
{
 if(_n3ds_wav_output_rate!=0){SDL_LockAudio();_wav_callback_enabled=false;_wav.active=false;_wav_reader_stop=true;SDL_UnlockAudio();}
 else {_wav_callback_enabled=false;_wav.active=false;_wav_reader_stop=true;}
 if(_wav_reader!=NULL){threadJoin(_wav_reader,UINT64_MAX);threadFree(_wav_reader);_wav_reader=NULL;}
 if(_wav.file!=NULL){WavLog("stop");_wav.Close();}
}
class MusicDriver_N3DSWav: public MusicDriver {
public:
 const char *Start(const char * const *){WavLog(_n3ds_wav_output_rate==0?"audio unavailable":"audio ready");return _n3ds_wav_output_rate==0?"SDL sound output unavailable":NULL;}
 void Stop(){StopSong();}
 void StopSong(){N3DSStopWavMusic();}

 void PlaySong(const char *filename){
  StopSong();_reported_end=false;_next_report=uint64_t(_n3ds_wav_output_rate)*10;
  if(!_wav.Open(filename)){
   FILE *log=fopen("wav-music.log","a");if(log!=NULL){fprintf(log,"rejected %s: %s\n",filename,_wav.error);fclose(log);}
   msf.playing=false;return; // Invalid/missing tracks must not be retried every game tick.
  }
  PumpWav();
  SDL_LockAudio();_wav_reader_stop=false;SDL_UnlockAudio();
  int32_t priority=0x30;svcGetThreadPriority(&priority,CUR_THREAD_HANDLE);
  _wav_reader=threadCreate(WavReader,NULL,16384,std::max(0x19,std::min(0x3E,int(priority)-1)),-2,false);
  if(_wav_reader==NULL){WavLog("reader allocation failed");StopSong();msf.playing=false;return;}
  SDL_LockAudio();_wav.active=_wav.queued!=0;_wav_callback_enabled=true;SDL_UnlockAudio();WavLog("play");
 }
 bool IsSongPlaying(){
  if(_wav.file==NULL)return false;
  SDL_LockAudio();bool playing=_wav.active;uint64_t frames=_wav.output_frames;SDL_UnlockAudio();
  if(playing&&frames>=_next_report){WavLog("progress");_next_report=frames+uint64_t(_n3ds_wav_output_rate)*10;}
  if(!playing&&!_reported_end){WavLog("end");_reported_end=true;}
  return playing;
 }
 void SetVolume(byte vol){if(_n3ds_wav_output_rate!=0)SDL_LockAudio();_wav.volume=std::min(unsigned(vol),127u);if(_n3ds_wav_output_rate!=0)SDL_UnlockAudio();}
};
class FMusicDriver_N3DSWav: public MusicDriverFactory<FMusicDriver_N3DSWav> {
public:
 static const int priority=6;
 const char *GetName(){return "wav";}
 const char *GetDescription(){return "3DS bounded PCM WAV streaming through SDL";}
 Driver *CreateInstance(){return new MusicDriver_N3DSWav();}
};
static FMusicDriver_N3DSWav iFMusicDriver_N3DSWav;
#endif
