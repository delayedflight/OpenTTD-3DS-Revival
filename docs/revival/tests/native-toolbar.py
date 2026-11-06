"""Compile the actual toolbar layout and native-strip selector in a host harness."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
def body(file,mark):
 s=(root/file).read_text();a=s.index(mark);i=s.index('{',a)+1;d=1
 while d:
  d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
cpp=r'''#define N3DS 1
#include <algorithm>
#include <cassert>
#include <set>
#include <iostream>
using std::max;using byte=unsigned char;using uint=unsigned;using ToolBarProperties=unsigned;
const uint TBP_TOOLBAR_MINBUTTON=14,TBP_BUTTONWIDTH=22,TBP_NORMAL_MAXBUTTON=19;
const int TB_LOWER=2,WWT_EMPTY=0,WWT_IMGBTN=1,GM_EDITOR=2,GM_NORMAL=1,WC_MAIN_TOOLBAR=1,WC_MAIN_WINDOW=2,WC_STATUS_BAR=3;
int _toolbar_mode=0,_game_mode=GM_NORMAL;
struct Widget{int type,left,right;};
struct Window{bool n3ds_train_depot=false,n3ds_train_depot_top=false,n3ds_user_position=false,n3ds_position_upper=false;int n3ds_user_left=0,n3ds_user_top=22;int width=320,left=40,top=0,height=22,window_class=1;Window *z_back=nullptr;uint widget_count=29;Widget widget[29];}bar;
Window *_z_front_window=&bar;
#define FOR_ALL_WINDOWS_FROM_FRONT(v) for(v=_z_front_window;v!=nullptr;v=v->z_back)
const Window *FindWindowById(int,int){return &bar;}
'''
cpp+=body('src/toolbar_gui.cpp','static void SplitToolbar(Window *w)\n{')+'\n'+body('src/video/sdl_v.cpp','static bool NativeN3DSToolbarRow(int y)')
cpp+=r'''
int main(){
 std::set<int> all;
 for(int page=0;page<2;page++){
  _toolbar_mode=page?TB_LOWER:0;SplitToolbar(&bar);int count=0;
  for(int x=0;x<320;x++){
   int hits=0;for(int i=0;i<28;i++)if(bar.widget[i].type==WWT_IMGBTN&&x>=bar.widget[i].left&&x<=bar.widget[i].right)hits++;
   assert(hits==1); // Every physical pixel belongs to one button.
  }
  for(int i=0;i<28;i++)if(bar.widget[i].type==WWT_IMGBTN){count++;all.insert(i);assert(bar.widget[i].right-bar.widget[i].left+1>=22);}
  assert(count==14&&bar.widget[27].type==WWT_IMGBTN);
 }
 assert(all.size()==27); // Same tool IDs as the original arrange14 pages (11 unused).
 assert(NativeN3DSToolbarRow(0)&&NativeN3DSToolbarRow(21));assert(!NativeN3DSToolbarRow(-1)&&!NativeN3DSToolbarRow(22));
 _game_mode=0;assert(!NativeN3DSToolbarRow(0));_game_mode=GM_NORMAL;
 _game_mode=GM_EDITOR;assert(NativeN3DSToolbarRow(0)&&NativeN3DSToolbarRow(21));_game_mode=GM_NORMAL;
 bar.width=400;assert(!NativeN3DSToolbarRow(0));bar.width=320;
 Window dialog;dialog.window_class=9;dialog.z_back=&bar;_z_front_window=&dialog;
 assert(!NativeN3DSToolbarRow(0));dialog.top=22;assert(NativeN3DSToolbarRow(0));
 std::cout<<"two pages, 14 full-width buttons each, complete hit coverage and native-strip boundaries passed\n";
}
'''
f=out/'native-toolbar.cpp';f.write_text(cpp);exe=out/'native-toolbar'
subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
