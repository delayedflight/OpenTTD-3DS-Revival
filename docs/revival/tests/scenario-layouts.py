"""Execute actual editor/new-game reflows with sanitizers, page coverage and hit bounds."""
from pathlib import Path
import re,subprocess,sys
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
def block(s,mark,start=0):
 a=s.index(mark,start);i=s.index('{',a)+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
def enum(s,token):return next(m.group() for m in re.finditer(r'enum[^{};]*\{[^{}]*\};',s) if token in m.group())
gen=(root/'src/genworld_gui.cpp').read_text();town=(root/'src/town_gui.cpp').read_text();land=(root/'src/terraform_gui.cpp').read_text();bar=(root/'src/toolbar_gui.cpp').read_text();win=(root/'src/window.cpp').read_text();video=(root/'src/video/sdl_v.cpp').read_text()
funcs='\n'.join(block(video,x) for x in ['bool N3DSIsMapConstructionWindow','bool N3DSIsConstructionWindow','bool N3DSIsManagementWindow']);base=block(win,'void Window::OnN3DSScreenChange');classes=sorted(set(re.findall(r'WC_[A-Z_]+',funcs+base)))
enums='\n'.join(enum(s,t) for s,t in [(gen,'GLAND_TEMPERATE'),(gen,'CSCEN_TEMPERATE'),(land,'ETTW_START'),(town,'TSEW_NEWTOWN'),(bar,'TBSE_DATEPANEL')])
cpp='''#define N3DS 1
#include <cassert>
#include <algorithm>
#include <iostream>
using std::min;using std::max;using uint=unsigned;using WindowClass=int;
template<class T>T Clamp(T a,T l,T h){return min(max(a,l),h);}
template<class T,int N>constexpr int lengthof(T(&)[N]){return N;}
const int GM_MENU=0,GM_NORMAL=1,GM_EDITOR=2,STR_NULL=0,SPR_SWITCH_TOOLBAR=1,GLWP_GENERATE=0,GLWP_HEIGHTMAP=1;
int _game_mode=GM_EDITOR;enum{WWT_LABEL,WWT_CAPTION,WWT_STICKYBOX,WWT_IMGBTN,WWT_TEXTBTN};
struct Window;bool N3DSUsesScrollableWorkspace(const Window*){return false;}bool N3DSIsCanvasWindow(int){return false;}
struct Point{int x,y;};struct Viewport{int left=0,top=0;};
struct Widget{int left=0,right=10,top=0,bottom=13,type=WWT_TEXTBTN,data=0,tooltips=0;bool hidden=false;};
'''+ 'enum{'+','.join(classes)+'};\n'+enums+'\n'+funcs+'''
struct Window{bool n3ds_train_depot=false,n3ds_train_depot_top=false,n3ds_user_position=false,n3ds_position_upper=false;int n3ds_user_left=0,n3ds_user_top=22;bool n3ds_native_layout=false;int n3ds_canvas_x=0,n3ds_canvas_y=0;int width=320,height=200,left=40,top=22,window_class=WC_SCEN_LAND_GEN,widget_count=64;Widget widget[80];struct{int step_width=1,width=36;}resize;Viewport*viewport=nullptr;
void OnN3DSScreenChange(bool);void OnResize(Point,Point){};void SetWidgetHiddenState(int i,bool h){assert(i>=0&&i<widget_count);widget[i].hidden=h;}
};void ResizeWindow(Window*w,int x,int y){w->width+=x;w->height+=y;}void MarkWholeScreenDirty(){}
'''+block(win,'void N3DSWidgetRect')+'\n'+base+'\n'
for name,s,cls,fields in [('Generate',gen,'struct GenerateLandscapeWindow','int n3ds_page=0,mode=0;'),('Create',gen,'struct CreateScenarioWindow',''),('Town',town,'struct FoundTownWindow',''),('Land',land,'struct ScenarioEditorLandscapeGenerationWindow',''),('Bar',bar,'struct ScenarioEditorToolbarWindow','bool n3ds_second_page=false;')]:
 cpp+='struct '+name+':Window{'+fields+block(s,'virtual void OnN3DSScreenChange(bool upper)',s.index(cls))+'};\n'
cpp+='''
void fits(Window&w){assert(w.left>=0&&w.left+w.width<=400&&w.top>=0&&w.top+w.height<=240);for(int i=0;i<w.widget_count;i++)if(!w.widget[i].hidden){auto&a=w.widget[i];assert(a.left>=0&&a.right<w.width&&a.top>=0&&a.bottom<w.height&&a.left<=a.right&&a.top<=a.bottom);}}
void targets(Window&w,int first,int last){for(int i=first;i<=last;i++)if(!w.widget[i].hidden){auto&a=w.widget[i];assert(a.right-a.left+1>=22&&a.bottom-a.top+1>=22);}}
int main(){
 assert(N3DSIsMapConstructionWindow(WC_FOUND_TOWN));
 for(int gm:{GM_MENU,GM_EDITOR}){_game_mode=gm;for(int n=0;n<20;n++)for(bool upper:{false,true,false}){
 Create c;c.widget_count=CSCEN_FLAT_LAND_HEIGHT_UP+1;c.OnN3DSScreenChange(upper);fits(c);targets(c,CSCEN_TEMPERATE,CSCEN_RANDOM_WORLD);targets(c,CSCEN_START_DATE_DOWN,CSCEN_START_DATE_UP);targets(c,CSCEN_FLAT_LAND_HEIGHT_DOWN,CSCEN_FLAT_LAND_HEIGHT_UP);
 Town t;t.widget_count=TSEW_LAYOUT_RANDOM+1;t.OnN3DSScreenChange(upper);fits(t);targets(t,TSEW_NEWTOWN,TSEW_MANYRANDOMTOWNS);targets(t,TSEW_SIZE_SMALL,TSEW_CITY);targets(t,TSEW_LAYOUT_ORIGINAL,TSEW_LAYOUT_RANDOM);
 Land l;l.widget_count=ETTW_RESET_LANDSCAPE+1;l.OnN3DSScreenChange(upper);fits(l);targets(l,ETTW_BUTTONS_START,ETTW_RESET_LANDSCAPE);
 for(int mode:{GLWP_GENERATE,GLWP_HEIGHTMAP}){Generate g;g.mode=mode;g.widget_count=(mode==GLWP_GENERATE?GLAND_WATER_SW:GLAND_HEIGHTMAP_ROTATION_PULLDOWN)+2;bool seen[80]={};for(int page=0;page<(mode==GLWP_GENERATE?3:2);page++){g.n3ds_page=page;g.OnN3DSScreenChange(upper);fits(g);for(int i=3;i<g.widget_count;i++)if(!g.widget[i].hidden){seen[i]=true;auto&a=g.widget[i];if(i!=GLAND_MAPSIZE_X_TEXT&&i!=GLAND_MAPSIZE_Y_TEXT&&i!=GLAND_START_DATE_TEXT1&&i!=GLAND_SNOW_LEVEL_TEXT1&&i!=GLAND_RANDOM_TEXT&&i!=GLAND_TOWN_TEXT&&i!=GLAND_INDUSTRY_TEXT&&i!=GLAND_TREE_TEXT&&i!=GLAND_LANDSCAPE_TEXT&&i!=GLAND_TERRAIN_TEXT&&i!=GLAND_WATER_TEXT&&i!=GLAND_SMOOTHNESS_TEXT&&i!=GLAND_BORDER_TYPES&&!(i>=GLAND_WATER_NW_TEXT&&i<=GLAND_WATER_SW_TEXT)){assert(a.right-a.left+1>=22&&a.bottom-a.top+1>=22);}}}for(int i=3;i<g.widget_count;i++){if(mode==GLWP_HEIGHTMAP&&i>=GLAND_RANDOM_TEXT&&i<=GLAND_RANDOM_BUTTON)continue;assert(seen[i]);}}
 Bar b;b.widget_count=27;bool seen[27]={};for(bool page:{false,true,false}){b.n3ds_second_page=page;b.OnN3DSScreenChange(upper);fits(b);for(int i=0;i<27;i++)if(!b.widget[i].hidden){seen[i]=true;if(i!=TBSE_DATEPANEL)targets(b,i,i);}}for(int i:{0,1,2,3,8,9,10,11,12,13,14,15,16,17,24,26})assert(seen[i]);
 }}
 std::cout<<"Actual editor/new-game controls: page coverage, >=22px targets, native bounds and 20 round trips in title/editor modes passed\\n";
}
'''
cpp='#include "'+str(root/'src/n3ds_menu_scroll.h')+'"\n'+cpp
f=out/'scenario-layouts.cpp';f.write_text(cpp);exe=out/'scenario-layouts';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
