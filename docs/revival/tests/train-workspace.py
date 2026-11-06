"""Execute actual train layouts, counts, row selection and paired screen routing."""
from pathlib import Path
import re,subprocess,sys
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
def block(s,mark,start=0):
 a=s.index(mark,start);i=s.index('{',a)+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
def enum(s,token):return next(m.group() for m in re.finditer(r'enum[^{};]*\{[^{}]*\};',s) if token in m.group())
dep=(root/'src/depot_gui.cpp').read_text();buy=(root/'src/build_vehicle_gui.cpp').read_text();win=(root/'src/window.cpp').read_text();video=(root/'src/video/sdl_v.cpp').read_text();train=(root/'src/train.h').read_text();base=block(win,'void Window::OnN3DSScreenChange');toggle=block(video,'static bool ToggleN3DSDepotScreen')
classes=sorted(set(re.findall(r'WC_[A-Z_]+',base+toggle+block(win,'bool N3DSTopWindow')+block(video,'static Window *N3DSFrontUi'))))
cpp='''#define N3DS 1
#include <algorithm>
#include <cassert>
#include <iostream>
#include <string>
#include <cstdio>
#include <vector>
using std::min;using std::max;using uint=unsigned;using WindowClass=int;using WindowNumber=int;using byte=unsigned char;using uint16=unsigned short;using EngineID=int;using GroupID=int;
template<class T>T Clamp(T x,T a,T b){return min(max(x,a),b);}template<class T,int N>constexpr int lengthof(T(&)[N]){return N;}
const int GM_MENU=0,GM_NORMAL=1,GM_EDITOR=2,VEH_TRAIN=0,VEH_ROAD=1,VEH_SHIP=2,VEH_AIRCRAFT=3,STR_NULL=0,TC_BLACK=0;
using VehicleType=int;int _game_mode=GM_NORMAL;bool _upper_ui=false,_map_pad=false,_depot_focus_active=false,_left_button_down=false,_left_button_clicked=false,_pad_held=false,_touch_held=false,_panel_needs_draw=false,_n3ds_map_input=false;
enum{WWT_CAPTION,WWT_STICKYBOX,WWT_LABEL};
struct Widget{int left=0,right=10,top=0,bottom=13,type=WWT_LABEL,data=0,tooltips=0;bool hidden=false;};struct Point{int x,y;};struct Viewport{int left,top;};
'''+ 'enum{'+','.join(classes)+'};\n'+enum(dep,'DEPOT_WIDGET_CLOSEBOX')+'\n'+enum(buy,'BUILD_VEHICLE_WIDGET_CLOSEBOX')+'''
struct Window{bool n3ds_train_depot=false,n3ds_train_depot_top=false,n3ds_native_layout=false,n3ds_user_position=false,n3ds_position_upper=false;int n3ds_user_left=0,n3ds_user_top=22,n3ds_canvas_x=0,n3ds_canvas_y=0;int left=40,top=22,width=320,height=200,window_class=WC_VEHICLE_DEPOT,window_number=7,widget_count=20;Window*z_back=nullptr;Widget widget[32];Viewport*viewport=nullptr;struct{int step_width=1,step_height=14,width=36,height=27;}resize;struct{int cap=0,pos=0,count=0;}vscroll,hscroll;
virtual void OnN3DSScreenChange(bool);virtual void OnResize(Point,Point){};void HideWidget(int i){widget[i].hidden=true;}void SetWidgetHiddenState(int i,bool b){widget[i].hidden=b;}
};Window*front=nullptr,*_map_ui_front=nullptr;
#define FOR_ALL_WINDOWS_FROM_FRONT(w) for(w=front;w!=nullptr;w=w->z_back)
Window*FindWindowById(int c,int n){for(Window*w=front;w;w=w->z_back)if(w->window_class==c&&w->window_number==n)return w;return nullptr;}
bool N3DSUpperUiActive(){return _upper_ui;}bool N3DSUsesScrollableWorkspace(const Window*){return false;}bool N3DSIsCanvasWindow(int){return false;}bool N3DSIsManagementWindow(int){return false;}bool N3DSIsConstructionWindow(int){return true;}
void MarkWholeScreenDirty(){}void ResizeWindow(Window*w,int x,int y){w->width+=x;w->height+=y;}
void ResetObjectToPlace(){}void HandleMouseEvents(){}void CenterN3DSMapCursor(){}void SelectN3DSInput(bool b){_n3ds_map_input=b;}void SetN3DSUpperUi(bool b){_upper_ui=b;}struct{void Reset(){}}_build_buttons;
bool IsInsideBS(int x,int a,int n){return x>=a&&x<a+n;}
'''+block(win,'void N3DSWidgetRect')+'\n'+base+'\n'+block(win,'bool N3DSTopWindow')+'\n'+block(video,'static Window *N3DSFrontUi')+'\n'+block(video,'static Window *N3DSUpperTrainDepot')+'\n'+block(video,'static bool N3DSDepotFocus()')+'\n'+block(video,'static void SetN3DSDepotFocus')+'\n'+toggle+'\n'+block(win,'Window *FindWindowFromPt')+'\n'
cpp+='''
struct Vehicle{int type=VEH_TRAIN;bool wagon=false,artic=false,rear=false;Vehicle*next=nullptr;Vehicle*Next()const{return next;}};
bool EngineHasArticPart(const Vehicle*v){return v->next&&v->next->artic;}Vehicle*GetNextArticPart(const Vehicle*v){return v->next;}bool IsRearDualheaded(const Vehicle*v){return v->rear;}bool IsTrainWagon(const Vehicle*v){return v->wagon;}
std::string label;void DoDrawString(const char*s,int,int,int){label=s;}
'''+block(train,'static inline Vehicle *GetNextVehicle')+'\n'+block(train,'static inline Vehicle *GetNextUnit')+'\n'
cpp+='struct Depot:Window{int type=VEH_TRAIN;'+block(dep,'virtual void OnN3DSScreenChange(bool upper)',dep.index('struct DepotWindow'))+block(dep,'void DrawN3DSConsistCount')+'};\n'
cpp+='struct Buy:Window{int vehicle_type=VEH_TRAIN,n3ds_info_scroll=0,n3ds_info_total=0;bool listview_mode=false;int N3DSPurchaseRow()const{return vehicle_type==VEH_TRAIN?22:14;}'+block(buy,'virtual void OnN3DSScreenChange(bool upper)',buy.index('struct BuildVehicleWindow'))
a=buy.index('uint i = (pt.y - this->widget[BUILD_VEHICLE_WIDGET_LIST].top)');z=buy.index(';',a)+1;cpp+='int Hit(Point pt){'+buy[a:z]+'return i;}};\n'
cpp+='''
void fits(Window&w,int i){auto&a=w.widget[i];assert(a.left>=0&&a.right<w.width&&a.top>=0&&a.bottom<w.height&&a.left<=a.right&&a.top<=a.bottom);}
int main(){
 Depot d;d.n3ds_train_depot=true;d.widget_count=DEPOT_WIDGET_RESIZE+1;d.widget[1].type=WWT_CAPTION;d.widget[2].type=WWT_STICKYBOX;
 Buy b;b.window_class=WC_BUILD_VEHICLE;b.widget_count=BUILD_VEHICLE_WIDGET_END+1;b.widget[1].type=WWT_CAPTION;b.widget[BUILD_VEHICLE_WIDGET_END].type=WWT_STICKYBOX;
 Window map;map.window_class=WC_MAIN_WINDOW;map.left=map.top=0;map.width=400;map.height=240;
 b.z_back=&d;d.z_back=&map;front=&b;
 for(int n=0;n<20;n++)for(bool top:{false,true,false}){d.n3ds_train_depot_top=top;d.OnN3DSScreenChange(false);b.OnN3DSScreenChange(false);assert(d.width==(top?400:320)&&d.height==(top?220:192)&&d.vscroll.cap==(top?5:4));assert(d.left==(top?0:40)&&d.top==(top?0:22));for(int i=0;i<d.widget_count;i++)if(!d.widget[i].hidden)fits(d,i);for(int i=0;i<b.widget_count;i++)if(!b.widget[i].hidden)fits(b,i);assert(b.width==320&&b.height==218&&b.left==40&&b.top==22);b.vscroll.pos=3;for(int row=0;row<4;row++)for(int pix=0;pix<22;pix++){Point pt={2,36+row*22+pix};assert(b.Hit(pt)==3+row);}}
 d.n3ds_train_depot_top=false;assert(ToggleN3DSDepotScreen(WC_BUILD_VEHICLE,7));assert(d.n3ds_train_depot_top&&!_map_pad&&N3DSTopWindow(&d)&&!N3DSTopWindow(&b));assert(FindWindowFromPt(80,80)==&b);SetN3DSDepotFocus(true);assert(N3DSDepotFocus()&&FindWindowFromPt(80,80)==&d);SetN3DSDepotFocus(false);assert(FindWindowFromPt(80,80)==&b);assert(ToggleN3DSDepotScreen(WC_VEHICLE_DEPOT,7)&&!d.n3ds_train_depot_top);
 front=&d;assert(ToggleN3DSDepotScreen(WC_VEHICLE_DEPOT,7)&&N3DSDepotFocus());assert(ToggleN3DSDepotScreen(WC_VEHICLE_DEPOT,7)&&!_map_pad);d.n3ds_train_depot=false;assert(!ToggleN3DSDepotScreen(WC_VEHICLE_DEPOT,7));
 Window small;small.n3ds_native_layout=true;small.window_class=WC_OTHER;small.width=160;small.height=100;small.n3ds_user_position=true;small.n3ds_user_left=200;small.n3ds_user_top=120;small.OnN3DSScreenChange(false);assert(small.left==200&&small.top==120);small.OnN3DSScreenChange(true);assert(!small.n3ds_user_position&&small.top==22);
 Vehicle e,a,r,w1,wa,w2;e.next=&a;a.artic=true;a.next=&r;r.rear=true;r.next=&w1;w1.wagon=true;w1.next=&wa;wa.artic=true;wa.next=&w2;w2.wagon=true;d.DrawN3DSConsistCount(&e,0,0);assert(label=="1 engine  2 wagons");d.DrawN3DSConsistCount(&w2,0,0);assert(label=="0 engines  1 wagon");
 std::cout<<"Native train rows/actions, 20 screen round trips, row hit pixels, paired draw/input ownership, pin/focus guards, manual positions and articulated/dual-head wagon counts passed\\n";
}
'''
cpp=cpp.replace('WC_OTHER','999');cpp='#include "'+str(root/'src/n3ds_menu_scroll.h')+'"\n'+cpp
f=out/'train-workspace.cpp';f.write_text(cpp);exe=out/'train-workspace';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
