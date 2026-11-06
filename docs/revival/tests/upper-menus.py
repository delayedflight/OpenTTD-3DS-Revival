"""Compile actual upper-menu switching, pointer, button and copy paths with stubs."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[3];s=(root/'src/video/sdl_v.cpp').read_text();out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
def block(marker,start=0,signature=True):
 a=s.index(marker,start);j=s.index('{',a);i=j+1;d=1
 while d:
  d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i] if signature else s[j:i]
cpp=r'''#include <algorithm>
#include <cassert>
#include <vector>
#include <cstring>
#include <iostream>
#include "HEADER"
using std::min;using std::max;using byte=unsigned char;using uint32=unsigned;
template<class T>T Clamp(T a,T l,T h){return min(max(a,l),h);}
struct Point{int x,y;};struct {Point pos,delta;bool dirty=false,in_window=false;int wheel=0;} _cursor;
struct Window{int window_class=2,window_number=7;void OnN3DSScreenChange(bool){}}menu;
using WindowClass=int;using WindowNumber=int;
const int GM_EDITOR=2,GM_NORMAL=1,GM_MENU=0,WC_MAIN_TOOLBAR=1,WKC_ESC=1,WKC_PAUSE=2;
int _game_mode=1,_upper_ui_class=0,_upper_ui_number=0;
void MoveN3DSCanvasDrag(int,int){};bool _canvas_touch=false;bool _upper_ui=false,_map_pad=false,_pad_held=false,_touch_held=false,_left_button_down=false,_left_button_clicked=false,_n3ds_map_input=false,_panel_needs_draw=false;
Point _ui_cursor{200,120},_n3ds_map_cursor{200,114};int _last_touch_x=0,_last_touch_y=0;
N3DSBuildButtons _build_buttons;Window *front=&menu;bool exists=true;int resets=0,mouse_events=0,keys=0,redraws=0;
#define FOR_ALL_WINDOWS_FROM_FRONT(w) for(w=front;w!=nullptr;w=nullptr)
Window *N3DSFrontUi(){return front;}Window *FindWindowById(int c,int n){return exists&&c==menu.window_class&&n==menu.window_number?&menu:nullptr;}
Window *_map_ui_front=nullptr;bool construction=false;bool N3DSIsMapConstructionWindow(WindowClass){return construction;}
static void SetN3DSUpperUi(bool upper,bool preserve_placement=false);
void ResetObjectToPlace(){resets++;}void HandleMouseEvents(){mouse_events++;}void MarkWholeScreenDirty(){redraws++;}void HandleKeypress(unsigned){keys++;}
bool NativeN3DSTitle(){return false;}bool NativeN3DSToolbarRow(int){return false;}bool NativeN3DSDropdownRow(int){return false;}bool NativeN3DSOrdersRow(int){return false;}
'''.replace('HEADER',str(root/'src/n3ds_controls.h'))
cpp+=block('static void SelectN3DSInput(bool map)\n{')+'\n'+block('static void SetN3DSUpperUi(bool upper, bool preserve_placement)\n{')+'\n'+block('static void CheckN3DSUpperUi()\n{')+'\n'+block('static void MoveN3DSTouch(int x, int y)\n{')
a=s.index('case SDL_JOYBUTTONDOWN:');buttons=block('if (_upper_ui) {',a)
cpp+='\nvoid Buttons(bool down,int button){struct{struct{int button;}jbutton;}ev{{button}};do{'+buttons+'}while(false);}\n'
a=s.index('static void DrawN3DSPanel()');copy=block('if (_upper_ui) {',a)
cpp+='''struct Format{int BytesPerPixel;};struct Surface{void*pixels;int pitch;Format*format;}*_sdl_screen,*_ui_surface;
void Copy(){'''+copy+'''}
int main(){
 _cursor.pos={200,120};SetN3DSUpperUi(true);assert(_upper_ui&&!_n3ds_map_input);
 MoveN3DSTouch(30,30);assert(_cursor.pos.x==200&&_cursor.pos.y==120&&!_left_button_down);
 _touch_held=true;MoveN3DSTouch(40,35);assert(_cursor.pos.x==210&&_cursor.pos.y==125&&_ui_cursor.x==210);
 _touch_held=false;MoveN3DSTouch(300,220);assert(_cursor.pos.x==210);_touch_held=true;MoveN3DSTouch(319,239);assert(_cursor.pos.x==229&&_cursor.pos.y==144);_touch_held=false;
 Buttons(true,5);Buttons(true,1);Buttons(false,1);assert(_left_button_down&&_pad_held);Buttons(false,5);assert(!_left_button_down&&!_pad_held&&!_n3ds_map_input);
 Buttons(true,3);assert(_cursor.wheel==-1);Buttons(true,6);assert(_cursor.wheel==0);
 for(int bytes:{1,4}){Format fmt{bytes};int pitch=400*bytes+16,ui_pitch=400*bytes+8;std::vector<byte>ui(ui_pitch*240,0x3D),dst(pitch*480,0xCE);Surface u{ui.data(),ui_pitch,&fmt},v{dst.data(),pitch,&fmt};_ui_surface=&u;_sdl_screen=&v;Copy();for(int y=0;y<480;y++)for(int x=0;x<pitch;x++)assert(dst[y*pitch+x]==(y<240&&x<400*bytes?0x3D:0xCE));}
 Buttons(true,7);assert(!_upper_ui&&redraws>=2);
 SetN3DSUpperUi(true);Buttons(true,5);int before=resets;SetN3DSUpperUi(false,true);assert(resets==before&&!_upper_ui&&!_pad_held);
 construction=true;SetN3DSUpperUi(true);before=resets;Buttons(true,3);assert(!_upper_ui&&_map_pad&&_n3ds_map_input&&resets==before&&_map_ui_front==front);construction=false;_map_pad=false;
 _map_pad=true;SetN3DSUpperUi(true);assert(!_upper_ui);_map_pad=false;
 _game_mode=GM_EDITOR;SetN3DSUpperUi(true);assert(_upper_ui);SetN3DSUpperUi(false);assert(!_upper_ui);
 _game_mode=GM_MENU;SetN3DSUpperUi(true);assert(!_upper_ui);_game_mode=GM_NORMAL;
 menu.window_class=WC_MAIN_TOOLBAR;SetN3DSUpperUi(true);assert(!_upper_ui);menu.window_class=2;
 SetN3DSUpperUi(true);exists=false;CheckN3DSUpperUi();assert(!_upper_ui);
 std::cout<<"optional toggle, title/map guards, relative pointer/reanchor, A/L overlap, wheel/return, target closure and 8/32-bit framebuffer copy bounds passed\\n";
}
'''
f=out/'upper-menus.cpp';f.write_text(cpp);exe=out/'upper-menus';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
