"""Exercise the actual pin dispatch and deferred release-gated screen request."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[3];s=(root/'src/video/sdl_v.cpp').read_text();win=(root/'src/window.cpp').read_text();out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
def block(s,mark):
 a=s.index(mark);i=s.index('{',a)+1;d=1
 while d:
  d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
cpp=r'''#define N3DS 1
#include <cassert>
#include <iostream>
using WindowClass=int;using WindowNumber=int;
enum{WC_TRAINS_LIST=1,WC_ROADVEH_LIST,WC_SHIPS_LIST,WC_AIRCRAFT_LIST,WC_VEHICLE_DETAILS,WC_VEHICLE_ORDERS,WC_VEHICLE_VIEW,WC_OTHER};
const int GM_NORMAL=1,GM_MENU=0,WDF_STICKY_BUTTON=1,WWT_STICKYBOX=1,WF_STICKY=4;
bool _upper_ui=false,_upper_request_pending=false,_upper_request_value=false,_left_button_down=false,_touch_held=false,_pad_held=false;
int _upper_request_class=0,_upper_request_number=0,_game_mode=GM_NORMAL,transfers=0;bool exists=true;
struct Widget{int type=WWT_STICKYBOX;};struct Window{int window_class=WC_TRAINS_LIST,window_number=7,desc_flags=WDF_STICKY_BUTTON,flags4=0;void InvalidateWidget(int){}}menu;
Window*FindWindowById(int c,int n){return exists&&menu.window_class==c&&menu.window_number==n?&menu:nullptr;}
void SetN3DSUpperUi(bool b){_upper_ui=b;transfers++;}
'''
cpp+='bool N3DSIsManagementWindow(WindowClass){return false;}bool N3DSIsConstructionWindow(WindowClass){return false;}\n'
cpp+=block(s,'bool N3DSUsesScreenPin(WindowClass cls)')+'\n'+block(s,'void N3DSRequestMenuScreenChange(WindowClass cls, WindowNumber number)')+'\n'+block(s,'static void ProcessN3DSMenuScreenChange()')
cpp+='\nvoid Click(Window*w,Widget*wi,int widget){'+block(win,'if (w->desc_flags & WDF_STICKY_BUTTON && wi->type == WWT_STICKYBOX)')+'}\n'
cpp+=r'''
int main(){
 Widget wi;_touch_held=_left_button_down=true;Click(&menu,&wi,2);assert(menu.flags4==0&&_upper_request_pending);ProcessN3DSMenuScreenChange();assert(!_upper_ui&&transfers==0);
 _touch_held=_left_button_down=false;ProcessN3DSMenuScreenChange();assert(_upper_ui&&transfers==1);ProcessN3DSMenuScreenChange();assert(transfers==1);
 _pad_held=true;Click(&menu,&wi,2);ProcessN3DSMenuScreenChange();assert(_upper_ui);_pad_held=false;ProcessN3DSMenuScreenChange();assert(!_upper_ui&&transfers==2);
 Click(&menu,&wi,2);exists=false;ProcessN3DSMenuScreenChange();assert(!_upper_ui);exists=true;
 Click(&menu,&wi,2);_game_mode=GM_MENU;ProcessN3DSMenuScreenChange();assert(!_upper_ui);_game_mode=GM_NORMAL;
 menu.window_class=WC_OTHER;Click(&menu,&wi,2);assert(menu.flags4==WF_STICKY&&!_upper_request_pending);
 N3DSRequestMenuScreenChange(WC_OTHER,7);assert(!_upper_request_pending);
 for(int cls=WC_TRAINS_LIST;cls<=WC_VEHICLE_VIEW;cls++)assert(N3DSUsesScreenPin(cls));
 std::cout<<"vehicle pin dispatch, release-gated transfer/return, no duplicate toggle, closed/title guards and legacy sticky fallback passed\n";
}
'''
f=out/'screen-pin.cpp';f.write_text(cpp);exe=out/'screen-pin';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
