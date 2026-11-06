"""Compile the actual mode-exit and cursor helper bodies against input-state stubs."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[3]
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
s=(root/'src/video/sdl_v.cpp').read_text()
def body(marker):
 a=s.rindex(marker) if marker=='case 3: {' else s.index(marker);i=s.index('{',a)+1;depth=1
 while depth:
  depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
select=body('static void SelectN3DSInput(bool map)\n{')
center=body('static void CenterN3DSMapCursor()')
toggle=body('case 3: {')
cpp=r'''
#include <cassert>
#include <iostream>
#include "CONTROL_HEADER"
struct Point {int x,y;};
struct {Point pos,delta;bool dirty=false,in_window=false;} _cursor;
struct {int width=400,height=240;} _screen;
struct Window {bool n3ds_train_depot=false,n3ds_train_depot_top=false,n3ds_user_position=false,n3ds_position_upper=false;int n3ds_user_left=0,n3ds_user_top=22;int top=228;} bar;
const int WC_STATUS_BAR=1, WC_DROPDOWN_MENU=2, GM_MENU=0, GM_EDITOR=2,GM_NORMAL=1;
bool bar_present=true;
const Window *FindWindowById(int,int){return bar_present?&bar:nullptr;}
bool _n3ds_map_input=true,_map_pad=true,_pad_held=true,_touch_held=true;
bool _left_button_down=true,_left_button_clicked=true,_panel_needs_draw=false;
Point _n3ds_map_cursor{300,180},_ui_cursor{82,65};
N3DSBuildButtons _build_buttons;
int _game_mode=GM_NORMAL,aborts=0,commits=0,closed_menus=0;
bool placing=true,last_mouse_held=true;
void *_map_ui_front;
void *N3DSFrontUi(){return &bar;}
void ResetObjectToPlace(){aborts++;placing=false;}
void HandleMouseEvents(){if(last_mouse_held&&!_left_button_down&&placing)commits++;last_mouse_held=_left_button_down;}
void DeleteWindowByClass(int){closed_menus++;}
void MarkWholeScreenDirty(){}
'''.replace('CONTROL_HEADER',str(root/'src/n3ds_controls.h'))
cpp+=select+'\n'+center+'\nvoid Toggle(int button){switch(button){case 7:\n'+toggle+'\n}}\n'
cpp+=r'''
int main(){
 _cursor.pos={317,199};_build_buttons.Set(5,true);
 Toggle(3);
 assert(aborts==1&&commits==0); // Abort before release; never commit on exit.
 assert(!_map_pad&&!_n3ds_map_input&&!_build_buttons.Held()&&!_pad_held&&!_touch_held);
 assert(_n3ds_map_cursor.x==200&&_n3ds_map_cursor.y==114); // Centre after Select saves old map position.
 assert(_cursor.pos.x==82&&_cursor.pos.y==65); // Keep UI cursor independent.
 assert(closed_menus==1&&_panel_needs_draw);
 Toggle(7);assert(_map_pad&&_n3ds_map_input&&aborts==1);
 assert(_cursor.pos.x==200&&_cursor.pos.y==114);
 _cursor.pos={252,174};placing=true;Toggle(7);
 assert(!_map_pad&&aborts==2&&commits==0);
 assert(_n3ds_map_cursor.x==200&&_n3ds_map_cursor.y==114);
 _game_mode=GM_MENU;Toggle(3);assert(!_map_pad&&aborts==2);
 bar_present=false;CenterN3DSMapCursor();assert(_n3ds_map_cursor.y==120);
 std::cout<<"exit abort ordering, recenter, independent cursors, SELECT/X and menu guard passed\n";
}
'''
f=out/'inspection-exit.cpp';f.write_text(cpp);exe=out/'inspection-exit'
subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
