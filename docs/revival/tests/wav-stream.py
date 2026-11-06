"""Exercise the real bounded WAV reader and driver, including the user's full sample."""
from pathlib import Path
import struct,wave,subprocess,sys
extra_samples=Path(sys.argv[3]).resolve() if len(sys.argv)>3 else None
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True);sample=Path(sys.argv[2]).resolve()
for rate in [8000,11025,22050,44100,48000]:
 for ch in [1,2]:
  with wave.open(str(out/f'{rate}-{ch}.wav'),'wb') as w:w.setparams((ch,2,rate,50003,'NONE',''));w.writeframes(struct.pack('<'+'h'*ch,*([10000] if ch==1 else [10000,-12000]))*50003)
base=(out/'44100-2.wav').read_bytes()
def riff(chunks):
 data=b'WAVE'+b''.join(tag+struct.pack('<I',len(b))+b+(b'\0' if len(b)%2 else b'') for tag,b in chunks);return b'RIFF'+struct.pack('<I',len(data))+data
fmt=base[20:36];pcm=base[44:]
(out/'metadata.wav').write_bytes(riff([(b'JUNK',b'abc'),(b'data',pcm),(b'fmt ',fmt),(b'LIST',b'metadata')]))
invalid=[b'',b'RIFF',base[:-1],b'RIFX'+base[4:],riff([(b'fmt ',fmt),(b'data',b'abc')]),riff([(b'fmt ',bytes([3,0])+fmt[2:]),(b'data',pcm)]),riff([(b'fmt ',fmt[:2]+b'\x03\x00'+fmt[4:]),(b'data',pcm)]),riff([(b'data',pcm)]),riff([(b'fmt ',fmt),(b'data',b'')]),riff([(b'fmt ',fmt),(b'data',pcm),(b'data',pcm)])]
for i,b in enumerate(invalid):(out/f'bad-{i}.wav').write_bytes(b)
(out/'autoplay').mkdir(exist_ok=True);(out/'autoplay/gm_tt00.wav').write_bytes(base)
cpp=r'''
#include <cstdio>
#include <cassert>
#include <mutex>
#include <thread>
#include <chrono>
#include <cstdint>
#include <vector>
#include <string>
#include <iostream>
std::mutex audio_mutex;thread_local bool audio_locked=false;
void SDL_LockAudio(){assert(!audio_locked);audio_mutex.lock();audio_locked=true;}
void SDL_UnlockAudio(){assert(audio_locked);audio_locked=false;audio_mutex.unlock();}
size_t CheckedRead(void*p,size_t a,size_t b,FILE*f){assert(!audio_locked);return fread(p,a,b,f);}
#define fread CheckedRead
'''+ '#include "'+str(root/'src/music/wav_stream.hpp')+'"\n#undef fread\n'+r'''
#define N3DS 1
using byte=unsigned char;
class Driver{public:virtual ~Driver(){}};class MusicDriver:public Driver{};
template<class T>class MusicDriverFactory{};
struct{bool playing=true,wav_autoplay_initialized=false;int playlist=4;}msf;
const int MAX_PATH=1024,NUM_SONGS_AVAILABLE=22,GM_DIR=0;
struct SongSpecs{const char*filename;};const SongSpecs _origin_songs_specs[]={{"gm_tt00.wav"},{"gm_tt02.wav"},{"gm_tt03.wav"},{"gm_tt17.wav"},{"gm_tt07.wav"},{"gm_tt09.wav"},{"gm_tt04.wav"},{"gm_tt19.wav"},{"gm_tt06.wav"},{"gm_tt12.wav"},{"gm_tt05.wav"},{"gm_tt01.wav"},{"gm_tt18.wav"},{"gm_tt10.wav"},{"gm_tt08.wav"},{"gm_tt13.wav"},{"gm_tt21.wav"},{"gm_tt15.wav"},{"gm_tt16.wav"},{"gm_tt14.wav"},{"gm_tt20.wav"},{"gm_tt11.wav"}};
std::string probe_dir="missing-dir";
char*FioFindFullPath(char*out,size_t capacity,int,const char*file){snprintf(out,capacity,"%s/%s",probe_dir.c_str(),file);return out;}

using Thread=std::thread*;bool fail_thread=false;const int CUR_THREAD_HANDLE=0;
int svcGetThreadPriority(int32_t*p,int){*p=0x30;return 0;}
void svcSleepThread(long long){std::this_thread::yield();}
Thread threadCreate(void(*fn)(void*),void*arg,size_t stack,int priority,int core,bool detached){assert(stack==16384&&priority==0x2f&&core==-2&&!detached);return fail_thread?nullptr:new std::thread(fn,arg);}
int threadJoin(Thread t,uint64_t){t->join();return 0;}void threadFree(Thread t){delete t;}

'''
s=(root/'src/music/n3ds_wav.cpp').read_text();s='\n'.join(l for l in s.splitlines() if not l.startswith('#include'))
cpp+=s+r'''
void pump(RevivalWavStream&w){for(unsigned n;(n=w.FreeWriteBytes())!=0;){n=std::min(n,8192u);unsigned got=w.ReadFile(n);w.Publish(got,n);}}
uint64_t render(RevivalWavStream&w,unsigned output,bool check){
 pump(w);w.active=true;uint64_t count=0;
 while(w.active){pump(w);int16_t dst[514]={};auto before=w.output_frames;w.Mix(dst,257,output);auto made=w.output_frames-before;count+=made;if(check)for(unsigned j=0;j<made;j++){assert(dst[j*2]==10000);assert(dst[j*2+1]==(w.channels==1?10000:-12000));}assert(w.queued<=w.CAPACITY);}
 assert(w.peak<=65536&&w.underruns==0&&!w.io_error);return count;
}
int main(int argc,char**argv){assert(argc==2||argc==3);assert(sizeof(RevivalWavStream)<66000);
 for(int rate:{8000,11025,22050,44100,48000})for(int ch:{1,2}){RevivalWavStream w;std::string p=std::to_string(rate)+"-"+std::to_string(ch)+".wav";assert(w.Open(p.c_str()));assert(render(w,22050,true)==(uint64_t(50003)*22050+rate-1)/rate);}
 RevivalWavStream w;assert(w.Open("metadata.wav"));assert(render(w,22050,true)==25002);
 for(int i=0;i<10;i++){assert(!w.Open(("bad-"+std::to_string(i)+".wav").c_str()));assert(w.file==nullptr&&!w.active&&w.error!=nullptr);}
 assert(!w.Open("missing.wav"));
 assert(w.Open("44100-2.wav"));w.active=true;int16_t dst[8]={};w.Mix(dst,4,22050);assert(w.underruns==1&&w.active);pump(w);w.volume=0;w.Mix(dst,4,22050);for(auto x:dst)assert(x==0);w.volume=127;
 for(unsigned i=0;i<4;i++){dst[2*i]=30000;dst[2*i+1]=-30000;}w.Mix(dst,4,22050);assert(dst[0]==32767&&dst[1]==-32768);w.Close();
 assert(w.Open("44100-2.wav"));pump(w);w.active=true;w.Mix(dst,4,22050);assert(w.queued<65536);assert(w.Open("11025-1.wav"));assert(w.queued==0&&w.phase==0&&!w.active);w.Close();
 assert(w.Open("44100-2.wav"));pump(w);w.Publish(0,4);assert(w.io_error&&w.eof); // Short reads drain safely.
 assert(w.Open(argv[1]));uint64_t frames=w.remaining/w.align;unsigned rate=w.rate;auto count=render(w,22050,false);assert(count==(frames*22050+rate-1)/rate);

 if(argc==3){uint64_t total=0;for(const auto&song:_origin_songs_specs){std::string path=std::string(argv[2])+"/"+song.filename;assert(w.Open(path.c_str()));auto frames=w.remaining/w.align;unsigned hz=w.rate;auto rendered=render(w,22050,false);assert(rendered==(uint64_t(frames)*22050+hz-1)/hz);total+=rendered;}std::cout<<"All 22 soundtrack files streamed completely; output frames="<<total<<"\n";}
 MusicDriver_N3DSWav driver;msf.playing=false;msf.wav_autoplay_initialized=false;msf.playlist=4;
 _n3ds_wav_output_rate=0;assert(driver.Start(nullptr)!=nullptr&&!msf.wav_autoplay_initialized&&!msf.playing);
 _n3ds_wav_output_rate=22050;assert(driver.Start(nullptr)==nullptr&&!msf.wav_autoplay_initialized&&!msf.playing);
 probe_dir="autoplay";assert(driver.Start(nullptr)==nullptr&&msf.wav_autoplay_initialized&&msf.playing&&msf.playlist==0);
 msf.playing=false;msf.playlist=3;assert(driver.Start(nullptr)==nullptr&&!msf.playing&&msf.playlist==3);
 driver.PlaySong(argv[1]);uint64_t prior=0;

 // Consume more than the entire prefetched ring without a single game-loop poll.
 auto tick=[](){
  auto limit=std::chrono::steady_clock::now()+std::chrono::seconds(3);
  for(;;){SDL_LockAudio();bool ready=_wav.eof||_wav.queued>=8192;SDL_UnlockAudio();if(ready)break;assert(std::chrono::steady_clock::now()<limit);std::this_thread::yield();}
  int16_t output[1024]={};SDL_LockAudio();N3DSMixWav(output,512);SDL_UnlockAudio();
 };
 for(int i=0;i<200;i++)tick();assert(_wav.output_frames>65536/4);
 while(driver.IsSongPlaying()){tick();assert(_wav.output_frames>=prior);prior=_wav.output_frames;}
 std::cerr<<"driver frames="<<_wav.output_frames<<" expected="<<count<<" underruns="<<_wav.underruns<<" queued="<<_wav.queued<<" remaining="<<_wav.remaining<<" error="<<_wav.io_error<<"\n";assert(_wav.output_frames==count&&_wav.underruns==0);driver.PlaySong("44100-2.wav");driver.SetVolume(0);int16_t output[1024]={};SDL_LockAudio();N3DSMixWav(output,512);SDL_UnlockAudio();for(auto x:output)assert(x==0);driver.StopSong();assert(!_wav_callback_enabled&&_wav.file==nullptr);
 driver.PlaySong("bad-0.wav");assert(!msf.playing&&!driver.IsSongPlaying());driver.Stop();fail_thread=true;msf.playing=true;driver.PlaySong("44100-2.wav");assert(!msf.playing&&_wav_reader==nullptr&&_wav.file==nullptr);fail_thread=false;
 for(int i=0;i<20;i++){driver.PlaySong("44100-2.wav");driver.StopSong();assert(_wav_reader==nullptr&&_wav.file==nullptr);}
 _n3ds_wav_output_rate=0;assert(driver.Start(nullptr)!=nullptr);
 std::cout<<"16-bit mono/stereo at 5 rates; metadata/padding/order; 11 invalid files; resampling duration, clipping, mute, starvation, short-read drain, restart, full user sample, background refill without game polling, thread failure and 20 joined restarts and first-install autoplay/preserved Stop/missing-track/audio guards passed. Reader bytes="<<sizeof(w)<<" sample output frames="<<count<<"\n";
}
'''
f=out/'wav-stream.cpp';f.write_text(cpp);exe=out/'wav-stream';subprocess.run(['clang++','-std=c++11','-O1','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe),str(sample)]+([str(extra_samples)] if extra_samples else []),cwd=out,check=True)
# Run the actual SDL startup/stop/callback with controlled backend failures.
sdl=(root/'src/sound/sdl_s.cpp').read_text();sdl='\n'.join(l for l in sdl.splitlines() if not l.startswith('#include'))
code=r'''
#define N3DS 1
#define WITH_SDL 1
#define CDECL
#define SDL_CALL
#include <cassert>
#include <cstring>
using Uint8=unsigned char;
const int SDL_INIT_AUDIO=1,AUDIO_S16SYS=2;
struct SDL_AudioSpec{int freq,format,channels,samples;void(*callback)(void*,Uint8*,int);};
struct FSoundDriver_SDL{};struct SoundDriver_SDL{const char*Start(const char*const*);void Stop();};
unsigned _n3ds_wav_output_rate=0;int frequency=0,requested=22050,closed=0,subclosed=0,backend=0;bool paused=true;
const char*SdlOpen(int){return backend==1?"missing DSP":nullptr;}void SdlClose(int){subclosed++;}
int GetDriverParamInt(const char*const*,const char*,int d){assert(d==22050);return requested;}
void N3DSStopWavMusic(){assert(_n3ds_wav_output_rate!=0);}
int SDL_OpenAudio(SDL_AudioSpec*a,SDL_AudioSpec*b){assert(a==b&&a->channels==2&&a->format==AUDIO_S16SYS);if(backend==2)return -1;if(backend==3)b->channels=1;return 0;}
void SDL_CloseAudio(){closed++;}void SDL_PauseAudio(int p){paused=p;assert(frequency==requested&&_n3ds_wav_output_rate==(unsigned)requested);}
bool MxInitialize(unsigned r){frequency=r;return true;}
void MxMixSamples(void*p,unsigned frames){auto*out=(short*)p;for(unsigned i=0;i<frames*2;i++)out[i]=1000;}
void N3DSMixWav(void*p,unsigned frames){auto*out=(short*)p;for(unsigned i=0;i<frames*2;i++)out[i]+=500;}
'''+sdl+r'''
int main(){SoundDriver_SDL driver;for(int hz:{11025,22050,44100}){requested=hz;assert(driver.Start(nullptr)==nullptr&&!paused);short output[8]={};fill_sound_buffer(nullptr,(Uint8*)output,sizeof(output));for(short x:output)assert(x==1500);driver.Stop();assert(_n3ds_wav_output_rate==0);}for(int failure:{1,2,3}){backend=failure;assert(driver.Start(nullptr)!=nullptr&&_n3ds_wav_output_rate==0);} }
'''
code='#include <initializer_list>\n'+code;f=out/'wav-sdl.cpp';f.write_text(code);exe=out/'wav-sdl';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True);print('Actual SDL callback preserves effect mix; mixer rate follows output; missing DSP/open/format failures and shutdown pass.')
