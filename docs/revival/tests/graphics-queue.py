"""Compile real SDK upload/render functions; force their queue-clear interleaving."""
from pathlib import Path
import sys,subprocess,tarfile,re
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
patch=(root/'environment/vendor/SDL-1.2.15-sdk.patch').read_text();part=patch.split('+++ b/src/video/n3ds/SDL_n3dsvideo.c\n',1)[1].split('diff --git ',1)[0];original='\n'.join(l[1:] for l in part.splitlines() if l.startswith('+'))+'\n'
(out/'src/video/n3ds').mkdir(parents=True,exist_ok=True);f=out/'src/video/n3ds/SDL_n3dsvideo.c';f.write_text(original)
subprocess.run(['patch','-p1','-i',str(root/'environment/patches/SDL-1.2.15-render-lock.patch')],cwd=out,check=True);fixed=f.read_text()
def block(s,m):
 s=re.sub(r'//[^\n]*','',s)
 a=s.index(m);i=s.index('{',a)+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
common=r'''
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <future>
#include <iostream>
#include <mutex>
#include <thread>
using u32=unsigned;struct Hidden{void*buffer=(void*)1;int w=32,h=32,byteperpixel=4,mode=0,screens=3,fitscreen=1,w1=32,h1=32,w2=32,h2=32,scalex=1,scaley=1;float l1=0,r1=1,t1=0,b1=1,l2=0,r2=1,t2=0,b2=1;};struct SDL_VideoDevice{Hidden*hidden;};
#define _THIS SDL_VideoDevice *device
#define this device
const int SDL_TOPSCR=1,SDL_BOTTOMSCR=2,SDL_FITWIDTH=1,C3D_FRAME_SYNCDRAW=1,C3D_CLEAR_ALL=1,GPU_VERTEX_SHADER=1,C3D_Both=0,GPU_TEXTURE0=0,GPU_REPLACE=0;
#define GX_BUFFER_DIM(a,b) 0
std::mutex renderLock;int privateVideoThreadEvent,VideoSurface1,VideoSurface2,RenderClearColor,uLoc_projection,projection,projection2,textureTranferFlags[4];struct{void*data=(void*)2;}spritesheet_tex;
std::atomic<bool>runThread(true),queueRunning(false),inFrame(false);std::atomic<int>panics(0),frames(0),transfers(0);bool gpu=true,beginOk=true,force=true;thread_local bool upload=false,renderer=false;
std::promise<void>paused,attempted,frameDone,resume;std::shared_future<void>resumeFuture;std::mutex eventLock;std::condition_variable eventCv;bool signalled=false;
void LightLock_Lock(std::mutex*m){if(renderer&&force)attempted.set_value();m->lock();}void LightLock_Unlock(std::mutex*m){m->unlock();}
void LightEvent_Wait(int*){std::unique_lock<std::mutex>l(eventLock);eventCv.wait(l,[]{return signalled;});signalled=false;}
void LightEvent_Signal(int*){{std::lock_guard<std::mutex>l(eventLock);signalled=true;}eventCv.notify_one();}
bool gspHasGpuRight(){if(renderer&&!gpu)runThread=false;return gpu;}void GSPGPU_FlushDataCache(void*,int){}
void WaitAndClear(){if(upload&&force){paused.set_value();resumeFuture.wait();}else queueRunning=false;if(queueRunning)panics++;queueRunning=false;}
void C3D_SyncDisplayTransfer(u32*,int,u32*,int,int){WaitAndClear();transfers++;}
bool C3D_FrameBegin(int){if(!beginOk){runThread=false;return false;}WaitAndClear();inFrame=true;return true;}
void C3D_FrameEnd(int){inFrame=false;queueRunning=true;frames++;runThread=false;if(force)frameDone.set_value();}
void C3D_RenderTargetClear(int,int,int,int){}void C3D_FrameDrawOn(int){}void C3D_FVUnifMtx4x4(int,int,int*){}void drawTexture(int,int,int,int,float,float,float,float){}
struct C3D_TexEnv{};C3D_TexEnv env;void C3D_TexBind(int,void*){}C3D_TexEnv*C3D_GetTexEnv(int){return &env;}void C3D_TexEnvInit(C3D_TexEnv*){}void C3D_TexEnvSrc(C3D_TexEnv*,int,int,int,int){}void C3D_TexEnvFunc(C3D_TexEnv*,int,int){}
'''
for label,s in [('before',original),('fixed',fixed)]:
 code=common+'\n'+block(s,'static void videoThread(void* data)\n{')+'\n'+block(s,'static void drawBuffers(_THIS)\n{')+'\n#undef this\n'
 code+=r'''
int main(){Hidden h;SDL_VideoDevice d{&h};resumeFuture=resume.get_future().share();auto p=paused.get_future();auto a=attempted.get_future();auto done=frameDone.get_future();
 std::thread up([&]{upload=true;drawBuffers(&d);});assert(p.wait_for(std::chrono::seconds(2))==std::future_status::ready);
 std::thread rd([&]{renderer=true;videoThread(&d);});LightEvent_Signal(&privateVideoThreadEvent);
'''
 code+=('assert(a.wait_for(std::chrono::seconds(2))==std::future_status::ready);assert(frames==0);' if label=='fixed' else 'assert(done.wait_for(std::chrono::seconds(2))==std::future_status::ready);')
 code+=r'''
 resume.set_value();up.join();rd.join();assert(frames==1&&transfers==1);
'''+f'assert(panics=={1 if label=="before" else 0});\n'
 if label=='fixed':
  code+=r'''
 force=false;queueRunning=false;
 renderer=true;beginOk=false;runThread=true;LightEvent_Signal(&privateVideoThreadEvent);videoThread(&d);assert(renderLock.try_lock());renderLock.unlock();beginOk=true;
 gpu=false;runThread=true;LightEvent_Signal(&privateVideoThreadEvent);videoThread(&d);assert(renderLock.try_lock());renderLock.unlock();renderer=false;gpu=true;
 // Early exit with revoked GPU rights must release lock and emit no transfer.
 gpu=false;int count=transfers;drawBuffers(&d);assert(transfers==count&&renderLock.try_lock());renderLock.unlock();gpu=true;
 h.buffer=nullptr;drawBuffers(&d);assert(renderLock.try_lock());renderLock.unlock();h.buffer=(void*)1;
 // Exercise both screen layouts and 10000 sequential handoffs without forced gap.
 for(int i=0;i<10000;i++){h.screens=1+i%3;drawBuffers(&d);runThread=true;renderer=true;videoThread(&d);renderer=false;}
 assert(panics==0&&frames==10001&&transfers==10001);
 // Closing wakes an idle renderer and joins without another frame.
 runThread=false;std::thread stopped([&]{videoThread(&d);});LightEvent_Signal(&privateVideoThreadEvent);stopped.join();
'''
 code+='std::cout<<"'+label+' panic count="<<panics<<" frames="<<frames<<" transfers="<<transfers<<"\\n"; }\n'
 cpp=out/(label+'.cpp');cpp.write_text(code);exe=out/label
 subprocess.run(['clang++','-std=c++17','-pthread','-fsanitize=address,undefined',str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 if label=='fixed':
  exe=out/'fixed-tsan';subprocess.run(['clang++','-std=c++17','-pthread','-fsanitize=thread',str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
print('Real SDK functions: forced old overlap reproduces queue panic; shared lock excludes it. Host model is not a GPU/hardware reproduction.')
