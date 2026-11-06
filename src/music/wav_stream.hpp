/* GPL v2. Bounded PCM WAV reader for the 3DS music prototype.
 * Main thread: Open/Close; reader: FreeWriteBytes/WritePointer/ReadFile/Publish.
 * Audio callback: Mix only. Caller serializes metadata with SDL_LockAudio;
 * disk reads write only reserved, unpublished ring space outside that lock. */
#ifndef REVIVAL_WAV_STREAM_HPP
#define REVIVAL_WAV_STREAM_HPP
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <algorithm>
#include <climits>

class RevivalWavStream {
public:
 static const unsigned CAPACITY=65536;
 unsigned char ring[CAPACITY];
 FILE *file=nullptr;
 unsigned rate=0,channels=0,align=0,read_pos=0,write_pos=0,queued=0,phase=0;
 uint32_t remaining=0;
 uint64_t output_frames=0;
 unsigned underruns=0,peak=0,volume=127;
 bool active=false,eof=false,io_error=false;
 const char *error=nullptr;
 ~RevivalWavStream(){Close();}
 void Close(){active=false;if(file!=nullptr)fclose(file);file=nullptr;queued=read_pos=write_pos=phase=0;}
 static uint16_t U16(const unsigned char *p){return p[0]|(uint16_t(p[1])<<8);}
 static uint32_t U32(const unsigned char *p){return U16(p)|(uint32_t(U16(p+2))<<16);}
 bool Fail(const char *why){error=why;Close();return false;}
 bool Open(const char *path){
  Close();error=nullptr;eof=io_error=false;underruns=peak=0;output_frames=0;
  file=fopen(path,"rb");if(file==nullptr)return Fail("file not found");
  if(fseek(file,0,SEEK_END)!=0)return Fail("file seek failed");long size=ftell(file);
  if(size<12||fseek(file,0,SEEK_SET)!=0)return Fail("truncated header");
  unsigned char h[16];if(fread(h,1,12,file)!=12||memcmp(h,"RIFF",4)||memcmp(h+8,"WAVE",4))return Fail("not RIFF WAVE");
  uint64_t end=uint64_t(U32(h+4))+8;if(end<12||end>uint64_t(size)||end>LONG_MAX)return Fail("invalid RIFF length");
  bool format=false;long data=-1;uint32_t data_size=0;
  for(uint64_t pos=12;pos+8<=end;){
   if(fseek(file,long(pos),SEEK_SET)!=0||fread(h,1,8,file)!=8)return Fail("truncated chunk header");
   uint32_t n=U32(h+4);uint64_t next=pos+8+uint64_t(n)+(n&1);
   if(next>end)return Fail("chunk outside RIFF");
   if(memcmp(h,"fmt ",4)==0){
    if(format||n<16||fread(h,1,16,file)!=16)return Fail("invalid format chunk");
    channels=U16(h+2);rate=U32(h+4);align=U16(h+12);
    if(U16(h)!=1||U16(h+14)!=16||(channels!=1&&channels!=2)||rate<8000||rate>48000||align!=channels*2||U32(h+8)!=rate*align)return Fail("requires 16-bit PCM mono/stereo, 8-48 kHz");
    format=true;
   }else if(memcmp(h,"data",4)==0){if(data>=0)return Fail("multiple data chunks");data=long(pos+8);data_size=n;}
   pos=next;
  }
  if(!format||data<0||data_size==0||data_size%align)return Fail("missing/unaligned audio data");
  remaining=data_size;if(fseek(file,data,SEEK_SET)!=0)return Fail("data seek failed");return true;
 }
 // Reserve a contiguous, frame-aligned span; callback cannot read unpublished bytes.
 unsigned FreeWriteBytes() const {
  if(file==nullptr||remaining==0||io_error)return 0;
  unsigned n=std::min(std::min(CAPACITY-queued,CAPACITY-write_pos),unsigned(remaining));return n-n%align;
 }
 unsigned char *WritePointer(){return ring+write_pos;}
 unsigned ReadFile(unsigned n){return unsigned(fread(WritePointer(),1,n,file));}
 void Publish(unsigned got,unsigned requested){
  if(got%align){got-=got%align;io_error=true;}
  if(got<requested)io_error=true;
  write_pos=(write_pos+got)%CAPACITY;queued+=got;peak=std::max(peak,queued);remaining-=got;
  if(remaining==0||io_error)eof=true;
 }
 int Sample(unsigned frame,unsigned channel) const {
  unsigned p=(read_pos+frame*align+std::min(channel,channels-1)*2)%CAPACITY;
  uint16_t value=U16(ring+p);return value>=32768?int(value)-65536:int(value);
 }
 void Mix(int16_t *dest,unsigned frames,unsigned output_rate){
  if(!active||output_rate<8000||output_rate>48000)return;
  for(unsigned i=0;i<frames;i++){
   unsigned available=queued/align;unsigned advance=(phase+rate)/output_rate;
   if(available==0){if(eof)active=false;else underruns++;break;}
   if(!eof&&available<std::max(2u,advance+1)){underruns++;break;}
   for(unsigned c=0;c<2;c++){
    int a=Sample(0,c),b=Sample(available>1?1:0,c);
    int sample=a;
    if(phase!=0)sample+=int(int64_t(b-a)*phase/output_rate);
    int mixed=int(dest[i*2+c])+sample*int(volume)/127;
    dest[i*2+c]=int16_t(std::max(-32768,std::min(32767,mixed)));
   }
   phase=(phase+rate)%output_rate;
   unsigned used=std::min(advance,available)*align;read_pos=(read_pos+used)%CAPACITY;queued-=used;output_frames++;
   if(queued==0&&eof){active=false;break;}
  }
 }
};
#endif
