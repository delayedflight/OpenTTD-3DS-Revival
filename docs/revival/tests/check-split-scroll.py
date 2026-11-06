"""Exercise the actual cached-scroll functions against a full-redraw pixel oracle."""
from pathlib import Path
import subprocess, sys
before=Path(sys.argv[1]).resolve(); after=Path(sys.argv[2]).resolve(); work=Path(sys.argv[3]).resolve(); work.mkdir(parents=True,exist_ok=True)
def extract(s, marker):
 a=s.index(marker); start=s.index('{',a);depth=1;i=start+1
 while depth:
  depth += (s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
common=r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <iostream>
using uint8 = unsigned char;
#define N3DS 1
const int WC_MAIN_WINDOW=0, WC_STATUS_BAR=1, WC_UI=2, WC_INVALID=-1;
struct Window { int left,top,width,height,window_class; const Window *z_front; };
#define FOR_ALL_WINDOWS_FROM_BACK_FROM(w,start) for(w=start;w!=nullptr;w=w->z_front) if(w->window_class!=WC_INVALID)
struct Point {int x,y;}; Point _vp_move_offs;
struct {void *dst_ptr; int pitch;} _screen;
void *_n3ds_ui_pixels;
struct {bool visible=false;} _cursor;
void UndrawMouseCursor() {}
struct Video {void MakeDirty(int,int,int,int){}} video;Video *_video_driver=&video;
struct Blitter {void ScrollBuffer(void*,int&,int&,int&,int&,int,int);};
struct BlitterFactoryBase {static Blitter *GetCurrentBlitter(){static Blitter b;return &b;}};
void GfxScroll(int,int,int,int,int,int,void *surface=nullptr);
void RedrawScreenRect(int,int,int,int);
std::array<uint8,400*240> topbuf,uibuf;
bool upper; int ox,oy;
int value(int x,int y) {return ((x+ox)*17 ^ (y+oy)*31)&255;}
int topref(int x,int y) {return upper ? (y>=228?42:value(x,y)) : ((x*3+y*5)&255);}
int uiref(int x,int y) {
 if(!upper && x>=20 && x<260 && y>=12 && y<172 && !(x>=100 && x<180 && y>=40 && y<110)) return value(x,y);
 return ((x*7+y*11+161)&255);
}
void RedrawScreenRect(int l,int t,int r,int b) {
 for(int y=t;y<b;y++)for(int x=l;x<r;x++){topbuf[y*400+x]=topref(x,y);uibuf[y*400+x]=uiref(x,y);}
}
'''
main=r'''
int main(){
 int mismatches=0,cases=0;
 const int delta[][2]={{17,0},{-19,0},{0,9},{0,-11},{13,7},{-11,-8},{13,-9},{-17,11},{500,0},{0,300}};
 for(bool mode:{true,false})for(auto &d:delta){
  upper=mode;ox=oy=0;_screen={topbuf.data(),400};_n3ds_ui_pixels=uibuf.data();RedrawScreenRect(0,0,400,240);
  Window status{0,228,400,12,WC_STATUS_BAR,nullptr};
  Window obstacle{upper?120:100,upper?15:40,upper?280:80,upper?210:70,WC_UI,&status};
  Window toolbar{0,0,400,96,WC_UI,&obstacle};
  Window owner{upper?0:20,upper?0:12,upper?400:240,upper?240:160,upper?WC_MAIN_WINDOW:WC_UI,upper?&toolbar:&obstacle};
  _vp_move_offs={d[0],d[1]};ox=-d[0];oy=-d[1];
  DoSetViewportPosition(owner.z_front,owner.left,owner.top,owner.width,owner.height,&owner);
  int errors=0;for(int y=0;y<240;y++)for(int x=0;x<400;x++){errors+=topbuf[y*400+x]!=topref(x,y);errors+=uibuf[y*400+x]!=uiref(x,y);}
  if(errors){std::cout<<(upper?"upper":"lower")<<" dx="<<d[0]<<" dy="<<d[1]<<" mismatched="<<errors<<"\n";mismatches++;}cases++;
 }
 std::cout<<"cases="<<cases<<" failed="<<mismatches<<"\n";return mismatches?1:0;
}
'''
for name,root in [('r3-source',before),('r3a-source',after)]:
 src=work/(name+'.cpp')
 if root.is_file():
  src.write_text(root.read_text())
 else:
  vp=extract((root/'src/viewport.cpp').read_text(),'static void DoSetViewportPosition(')
  scroll=extract((root/'src/gfx.cpp').read_text(),'void GfxScroll(')
  blit=extract((root/'src/blitter/8bpp_base.cpp').read_text(),'void Blitter_8bppBase::ScrollBuffer(').replace('Blitter_8bppBase::','Blitter::')
  src.write_text(common+blit+'\n'+scroll+'\n'+vp+'\n'+main)
 exe=work/name
 subprocess.run(['clang++','-std=c++11','-O1','-fsanitize=address,undefined',str(src),'-o',str(exe)],check=True)
 r=subprocess.run([str(exe)],capture_output=True,text=True);(work/(name+'.log')).write_text(r.stdout+r.stderr);print(name+':\n'+r.stdout+r.stderr)
 assert r.returncode==(1 if name=='r3-source' else 0),(name,r.returncode)
