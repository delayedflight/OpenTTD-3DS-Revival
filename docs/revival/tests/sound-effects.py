"""Run actual CAT parser, effect channel publication and mixer under sanitizers."""
from pathlib import Path
import re,subprocess,sys
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True);bank=Path(sys.argv[2]).resolve()
def block(s,mark):
 a=s.index(mark);i=s.index('{',a)+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
s=(root/'src/sound.cpp').read_text();m=(root/'src/mixer.cpp').read_text();m='\n'.join(l for l in m.splitlines() if not l.startswith('#include'))
cpp=r'''
#define N3DS 1
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <atomic>
#include <thread>
#include <mutex>
#include <iostream>
using std::max;using std::min;using uint=unsigned;using byte=unsigned char;using int8=signed char;using int16=short;using uint32=uint32_t;
template<class T>T Clamp(T x,T a,T b){return min(max(x,a),b);}template<class T,size_t N>T*endof(T(&a)[N]){return a+N;}
const int MX_AUTOFREE=1,SOUND_SLOT=0;const unsigned ORIGINAL_SAMPLE_COUNT=73;const int PANNING_LEVELS=16;
#define DEBUG(...)
std::mutex audio_mutex;thread_local bool audio_locked=false;
void SDL_LockAudio(){assert(!audio_locked);audio_mutex.lock();audio_locked=true;}void SDL_UnlockAudio(){assert(audio_locked);audio_locked=false;audio_mutex.unlock();}
unsigned _n3ds_wav_output_rate=22050;
template<class T>T*CallocT(unsigned n){return (T*)calloc(n,sizeof(T));}template<class T>T*MallocT(size_t n){assert(!audio_locked);return (T*)malloc(n*sizeof(T));}
struct FileEntry{uint8_t file_slot;size_t file_offset,file_size;uint16_t rate;uint8_t bits_per_sample,channels,volume,priority;};
unsigned _file_count=0;FileEntry*_files=nullptr;FileEntry pool[73];unsigned pool_count=0;
FileEntry*AllocateFileEntry(){assert(pool_count<73);return pool+pool_count++;}const FileEntry*GetSound(unsigned i){return i<pool_count?pool+i:nullptr;}
std::vector<byte> cat;size_t pos=0;
void FioOpenFile(int,const char*name){assert(!audio_locked);FILE*f=fopen(name,"rb");assert(f);fseek(f,0,SEEK_END);cat.resize(ftell(f));rewind(f);assert(fread(cat.data(),1,cat.size(),f)==cat.size());fclose(f);pos=0;}
size_t FioGetPos(){return pos;}void FioSeekTo(size_t at,int how){pos=how==SEEK_CUR?pos+at:at;assert(pos<=cat.size());}
byte FioReadByte(){return pos<cat.size()?cat[pos++]:0;}uint16_t FioReadWord(){byte b=FioReadByte();return b|(FioReadByte()<<8);}uint32_t FioReadDword(){uint32_t b=FioReadWord();return b|(uint32_t(FioReadWord())<<16);}
void FioReadBlock(void*p,size_t n){assert(!audio_locked&&pos+n<=cat.size());memcpy(p,cat.data()+pos,n);pos+=n;}void FioSeekToFile(int,size_t at){FioSeekTo(at,SEEK_SET);}
'''+m+'\n'
for key in ['static void OpenBankFile','static bool SetBankSource','bool SoundInitialize','static void StartSound']:cpp+=block(s,key)+'\n'
for key in ['_sound_base_vol','_sound_idx']:cpp+=re.search(r'static const byte '+key+r'\[\] = \{.*?\};',s,re.S).group()+'\n'
cpp+=block(s,'void SndCopyToPool')+r'''
bool active(){for(auto&c:_channels)if(c.active)return true;return false;}
int main(int argc,char**argv){assert(argc==2);MxInitialize(22050);assert(SoundInitialize(argv[1]));assert(_file_count==73);SndCopyToPool();unsigned nonempty=0,largest=0;
 for(unsigned i=0;i<73;i++){auto&f=pool[i];if(!f.file_size)continue;nonempty++;largest=max(largest,(unsigned)f.file_size);assert(f.rate==11025&&f.bits_per_sample==8&&f.channels==1);StartSound(i,0,127);bool nonzero=false;unsigned frames=0;while(active()){int16_t buf[1024];SDL_LockAudio();MxMixSamples(buf,512);SDL_UnlockAudio();for(auto x:buf)nonzero|=x!=0;frames+=512;assert(frames<200000);}assert(nonzero);}
 assert(nonempty==71&&largest==44654);for(auto&c:_channels)assert(c.memory==nullptr&&!c.active);
 std::atomic<bool>running{true};std::atomic<unsigned>mixed{0};
 std::thread callback([&](){while(running){int16_t buf[1024];SDL_LockAudio();MxMixSamples(buf,512);SDL_UnlockAudio();mixed++;std::this_thread::yield();}});
 for(unsigned n=0;n<3000;n++){StartSound(n%73,int(n%33)-16,127);if(n%8==0)std::this_thread::yield();}
 running=false;callback.join();while(active()){int16_t buf[1024];SDL_LockAudio();MxMixSamples(buf,512);SDL_UnlockAudio();}
 assert(mixed>0);for(auto&c:_channels)assert(c.memory==nullptr&&!c.active);free(_files);
 std::cout<<"73 CAT slots / 71 PCM effects parsed and mixed nonzero; correct format/rate, callback/main publication stress (3000 triggers), channel limits and sample release passed. Largest effect="<<largest<<" bytes.\n";
}
'''
f=out/'sound-effects.cpp';f.write_text(cpp)
for sanitizer in ['address,undefined','thread']:
 exe=out/('sound-effects-'+sanitizer.split(',')[0]);subprocess.run(['clang++','-std=c++11','-O1','-fsanitize='+sanitizer,str(f),'-o',str(exe)],check=True);subprocess.run([str(exe),str(bank)],cwd=out,check=True)
