"""Check native row ownership with child viewports and viewport screen translation."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[3];s=(root/'src/video/sdl_v.cpp').read_text();v=(root/'src/vehicle_gui.cpp').read_text();out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
def block(s,mark,start=0):
 a=s.index(mark,start);i=s.index('{',a)+1;d=1
 while d:
  d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
cpp=r'''#include <cassert>
#include <algorithm>
#include <iostream>
using std::min;
enum{WC_MAIN_WINDOW=1,WC_STATUS_BAR,WC_TOOLTIPS,WC_DROPDOWN_MENU,WC_VEHICLE_VIEW,WC_VEHICLE_ORDERS,WC_VEHICLE_DETAILS,WC_TRAINS_LIST,WC_ROADVEH_LIST,WC_SHIPS_LIST,WC_AIRCRAFT_LIST,WC_OTHER};
const int GM_NORMAL=1;int _game_mode=GM_NORMAL;struct Window;bool N3DSUsesScrollableWorkspace(const Window*){return false;}bool N3DSIsCanvasWindow(int){return false;}bool N3DSIsManagementWindow(int){return false;}bool N3DSIsConstructionWindow(int){return false;}
struct Window{int window_class,left,width,top,height;Window*z_back;};Window*_z_front_window;
#define FOR_ALL_WINDOWS_FROM_FRONT(w) for(w=_z_front_window;w!=nullptr;w=w->z_back)
'''+block(s,'static bool NativeN3DSOrdersRow(int y)')+r'''
struct Point{int x,y;};struct Viewport{int left=3,top=44,width=226,height=100,virtual_width=226,virtual_height=100;};
struct Base{int left=0,top=27,width=250,height=134;Viewport*viewport;virtual void OnResize(Point,Point){};};
void ResizeWindow(Base*w,int x,int y){w->width+=x;w->height+=y;}void MarkWholeScreenDirty(){}
struct Camera:Base{
'''+block(v,'virtual void OnN3DSScreenChange(bool upper)',v.index('struct VehicleViewWindow'))+'\n'+block(v,'virtual void OnResize(Point new_size, Point delta)',v.index('struct VehicleViewWindow'))+r'''
};
int main(){
 Window bar{WC_OTHER,40,320,0,22,nullptr},list{WC_TRAINS_LIST,40,320,22,200,&bar},view{WC_VEHICLE_VIEW,40,250,22,134,&list};_z_front_window=&view;
 assert(!NativeN3DSOrdersRow(21)&&NativeN3DSOrdersRow(22)&&NativeN3DSOrdersRow(155)&&NativeN3DSOrdersRow(200)&&!NativeN3DSOrdersRow(222));
 Window dropdown{WC_DROPDOWN_MENU,40,320,22,100,&view};_z_front_window=&dropdown;assert(NativeN3DSOrdersRow(50)&&NativeN3DSOrdersRow(200));
 Window other{WC_OTHER,0,400,22,200,&view};_z_front_window=&other;assert(!NativeN3DSOrdersRow(100));
 Camera c;Viewport vp;c.viewport=&vp;for(int i=0;i<20;i++){c.OnN3DSScreenChange(false);assert(c.left==40&&c.top==22&&vp.left==43&&vp.top==39);c.OnN3DSScreenChange(true);assert(c.left==0&&vp.left==3&&vp.top==39);}
 c.width=400;c.height=240;c.OnN3DSScreenChange(false);assert(c.width==320&&c.height==218&&vp.width==146&&vp.height==78);
 std::cout<<"child-window native row routing, modal fallback, viewport translation round trips and bottom camera size limits passed\n";
}
'''
f=out/'native-vehicle-rows.cpp';f.write_text(cpp);exe=out/'native-vehicle-rows';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
