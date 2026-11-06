"""Compile the actual 3DS station/airport reflows and screen-anchor method."""
from pathlib import Path
import re,subprocess,sys
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
depot=(root/'src/depot_gui.cpp').read_text()
rail=(root/'src/rail_gui.cpp').read_text();air=(root/'src/airport_gui.cpp').read_text();win=(root/'src/window.cpp').read_text();video=(root/'src/video/sdl_v.cpp').read_text()
def block(s,mark):
 a=s.index(mark);i=s.index('{',a)+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
def reflow(s,ctor):
 a=s.index('#ifdef N3DS',s.index(ctor));return s[a+len('#ifdef N3DS'):s.index('#endif',a)]
enums=[]
for s,prefix in [(rail,'BRSW_CLOSE'),(air,'BAW_BOTTOMPANEL')]:
 pos=s.index(prefix);a=s.rfind('enum',0,pos);z=s.index('};',pos)+2;enums.append(s[a:z])
classes=sorted(set(re.findall(r'WC_[A-Z_]+',block(win,'static void LayoutN3DSToolbars')+ block(video,'bool N3DSIsConstructionWindow')+block(video,'bool N3DSIsMapConstructionWindow')+block(win,'void Window::OnN3DSScreenChange'))))
cpp='''#define N3DS 1
#include <algorithm>
#include <cassert>
#include <iostream>
#include <cstdint>
using std::min;using std::max;using uint=unsigned;using uint16=uint16_t;using WindowClass=int;
const int GM_MENU=0,GM_NORMAL=1;int _game_mode=GM_NORMAL;bool N3DSIsManagementWindow(int){return false;}
enum{WWT_PANEL,WWT_LABEL,WWT_EMPTY,WWT_CAPTION,WWT_STICKYBOX,WWT_TEXTBTN,WWT_DROPDOWN,WWT_EDITBOX,WWT_IMGBTN,WWT_IMGBTN_2,WWT_PUSHIMGBTN};
struct Widget{int type=WWT_PANEL,left=0,right=147,top=0,bottom=13,tooltips=0;};
struct Point{int x,y;};struct Viewport{int left=0,top=0;};const int STR_NULL=0;
'''+ 'enum{'+','.join(classes)+'};\n'+'\n'.join(enums)+'\n'+block(video,'bool N3DSIsMapConstructionWindow')+'\n'+block(video,'bool N3DSIsConstructionWindow')+'''
struct Window{Widget widget[64];int width=148,height=200,left=0,top=0,window_class=WC_BUILD_STATION,widget_count=64;struct{uint16 pos=0,count=2,cap=0;}vscroll,hscroll;struct{int step_width=1,width=36,step_height=14;}resize;Viewport*viewport=nullptr;
void SetWidgetHiddenState(int,bool){};void OnResize(Point,Point){};void OnN3DSScreenChange(bool);
void Depot(int type){
#define VEH_TRAIN 0
'''+reflow(depot,'void CreateDepotListWindow(VehicleType type)')+'''
}
void Rail(bool newstation){
'''+reflow(rail,'BuildRailStationWindow(const')+'''
}
void Airport(){
'''+reflow(air,'AirportPickerWindow(const')+'''
}};
void ResizeWindow(Window*w,int x,int y){w->width+=x;w->height+=y;}void MarkWholeScreenDirty(){}
'''+block(win,'void Window::OnN3DSScreenChange')+'''
Window *test_window;bool upper_active=false;
bool N3DSUpperUiActive(){return upper_active;}
#define FOR_ALL_WINDOWS_FROM_BACK(w) for(w=test_window;w!=nullptr;w=nullptr)
'''+block(win,'static void LayoutN3DSToolbars')+'''
void fits(Widget&w,int width,int height){assert(w.left>=0&&w.right<width&&w.top>=14&&w.bottom<height&&w.right>=w.left&&w.bottom>=w.top);}
int main(){
 for(int type=0;type<4;type++){Window w;w.width=36;w.height=27;w.hscroll.cap=type==0?290:(type==3?4:(type==1?5:3));w.vscroll.cap=type==0?6:(type==1?5:3);w.resize.step_width=type==0?1:(type==1?56:(type==2?90:74));w.resize.step_height=type==0?14:24;w.Depot(type);assert(36+w.hscroll.cap*w.resize.step_width+(type==0?36:0)<=320);assert(27+w.vscroll.cap*w.resize.step_height+(type==0?12:0)<=218);assert(w.hscroll.cap>0&&w.vscroll.cap>0);}
 for(int count:{2,7,11,14}){Window w;test_window=&w;w.window_class=WC_BUILD_TOOLBAR;w.widget_count=count+1;for(int i=0;i<count;i++)w.widget[i].type=WWT_IMGBTN;w.widget[count].type=WWT_STICKYBOX;for(bool upper:{false,true,false}){upper_active=upper;LayoutN3DSToolbars();assert(w.width==(upper?400:320));for(int i=0;i<count;i++){fits(w.widget[i],w.width,w.height);assert(w.widget[i].right-w.widget[i].left+1==(upper?50:40));assert(w.widget[i].bottom-w.widget[i].top+1==32);}assert(w.widget[count].right==w.width-1);}}
 for(bool custom:{false,true}){Window w;w.Rail(custom);assert(w.width==320&&w.height<=218);w.OnN3DSScreenChange(false);assert(w.left==40&&w.top==22);for(int i=0;i<7;i++){auto&a=w.widget[BRSW_PLATFORM_NUM_1+i];auto&b=w.widget[BRSW_PLATFORM_LEN_1+i];fits(a,w.width,w.height);fits(b,w.width,w.height);assert(a.right-a.left+1==22&&a.bottom-a.top+1==22&&b.bottom-b.top+1==22);}fits(w.widget[BRSW_PLATFORM_DRAG_N_DROP],w.width,w.height);for(int i=0;i<2;i++)fits(w.widget[BRSW_HIGHLIGHT_OFF+i],w.width,w.height);if(custom){assert(w.vscroll.pos==0);assert(w.widget[BRSW_NEWST_LIST].bottom-w.widget[BRSW_NEWST_LIST].top+1==5*22);}}
 Window a;a.Airport();for(int i=0;i<BAW_AIRPORT_COUNT;i++){Widget&w=a.widget[BAW_SMALL_AIRPORT+i];fits(w,320,218);assert(w.bottom-w.top+1==22);for(int j=0;j<i;j++){Widget&v=a.widget[BAW_SMALL_AIRPORT+j];assert(w.right<v.left||w.left>v.right||w.bottom<v.top||w.top>v.bottom);}}
 for(int cls:{WC_BUILD_VEHICLE,WC_VEHICLE_DEPOT})for(int step:{1,74,80,90}){Window w;w.window_class=cls;w.width=360;w.resize.step_width=step;for(int n=0;n<20;n++){w.OnN3DSScreenChange(false);assert(w.width<=320&&w.left>=40&&w.left+w.width<=360);int small=w.width;w.OnN3DSScreenChange(true);assert(w.width<=400);w.OnN3DSScreenChange(false);assert(w.width==small);}}
 std::cout<<"actual station/airport controls fit, 22px hit targets, custom-list capacity and 20 reversible cell-aligned depot/purchase screen changes passed\\n";
}
'''
f=out/'construction-layouts.cpp';f.write_text(cpp);exe=out/'construction-layouts';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
