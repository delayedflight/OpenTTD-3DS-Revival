"""Compile actual management-menu reflows; verify bounds and repeated transfers."""
from pathlib import Path
import re,subprocess,sys
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
def block(s,mark,start=0):
 a=s.index(mark,start);i=s.index('{',a)+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
def enum(s,token):
 return next(m.group() for m in re.finditer(r'enum[^{};]*\{[^{}]*\};',s) if token in m.group())
sources={k:(root/('src/'+k+'_gui.cpp')).read_text() for k in ['company','settings','industry','station','intro']};win=(root/'src/window.cpp').read_text();video=(root/'src/video/sdl_v.cpp').read_text()
items=[('Company','company','struct CompanyWindow : Window','CW_WIDGET_CLOSEBOX'),('Options','settings','struct GameOptionsWindow','GAMEOPT_CLOSE'),('Settings','settings','struct GameSettingsWindow','SETTINGSEL_CLOSE'),('Difficulty','settings','struct GameDifficultyWindow','GDW_CLOSEBOX'),('Funding','industry','class BuildIndustryWindow','DPIW_CLOSEBOX'),('Industries','industry','class IndustryDirectoryWindow','IDW_CLOSEBOX'),('Stations','station','class CompanyStationsWindow','SLW_CLOSEBOX')]
# Names differ for the generic settings/option enums; include all enums with needed tokens.
enums=[]
for token,key in [('CW_WIDGET_CLOSEBOX','company'),('GAMEOPT_CURRENCY','settings'),('SETTINGSEL_OPTIONSPANEL','settings'),('GDW_CLOSEBOX','settings'),('DPIW_CLOSEBOX','industry'),('IDW_CLOSEBOX','industry'),('SLW_CLOSEBOX','station'),('SGI_GENERATE_GAME =','intro')]:enums.append(enum(sources[key],token))
funcs='\n'.join(block(video,x) for x in ['bool N3DSIsMapConstructionWindow','bool N3DSIsConstructionWindow','bool N3DSIsManagementWindow'])
base=block(win,'void Window::OnN3DSScreenChange');classes=sorted(set(re.findall(r'WC_[A-Z_]+',funcs+base)))
cpp='''#define N3DS 1
#include <algorithm>
#include <cassert>
#include <iostream>
using std::min;using std::max;using uint=unsigned;using WindowClass=int;
enum{WWT_LABEL,WWT_CAPTION,WWT_STICKYBOX};const int STR_NULL=0,STR_OPTIONS_FULLSCREEN=1,GM_MENU=0,GM_NORMAL=1;int _game_mode=GM_NORMAL;
template<class T>T Clamp(T a,T l,T h){return min(max(a,l),h);}struct Window;bool N3DSUsesScrollableWorkspace(const Window*){return false;}bool N3DSIsCanvasWindow(int){return false;}
struct Widget{int left=0,right=0,top=0,bottom=0,type=WWT_LABEL,data=0,tooltips=0;bool hidden=false;};
struct Point{int x,y;};struct Viewport{int left=0,top=0;};
'''+ 'enum{'+','.join(classes)+'};\n'+'\n'.join(enums)+'\n'+funcs+'''
struct Window{bool n3ds_native_layout=false;int n3ds_canvas_x=0,n3ds_canvas_y=0;int width=320,height=200,left=40,top=22,window_class=WC_COMPANY,widget_count=80;Widget widget[80];struct{int cap=0;}vscroll;struct{int step_width=1,width=36;}resize;Viewport*viewport=nullptr;
void OnN3DSScreenChange(bool);void OnResize(Point,Point){};void HideWidget(int i){widget[i].hidden=true;}void SetWidgetHiddenState(int i,bool h){widget[i].hidden=h;}void LowerWidget(int){};
};void ResizeWindow(Window*w,int x,int y){w->width+=x;w->height+=y;}void MarkWholeScreenDirty(){}
'''+block(win,'void N3DSWidgetRect')+'\n'+base+'\n'
for name,key,cls,_ in items:cpp+='struct '+name+':Window{'+block(sources[key],'virtual void OnN3DSScreenChange(bool upper)',sources[key].index(cls))+'};\n'
a=sources['intro'].index('#ifdef N3DS',sources['intro'].index('SelectGameWindow(const'));z=sources['intro'].index('#endif',a);rows=re.findall(r'\{([^{}]+)\}',sources['intro'][sources['intro'].index('static const Widget _select_game_widgets'):sources['intro'].index('#else')]);init=''.join('widget[%d].left=%s;widget[%d].right=%s;'%(i,r.split(',')[3].strip(),i,r.split(',')[4].strip()) for i,r in enumerate(rows) if i>=8 and i<=11)
cpp+='struct Title:Window{void Layout(){'+init+sources['intro'][a+len('#ifdef N3DS'):z]+'}};\n'
cpp+=block(sources['settings'],'static int N3DSDifficultyOption')
cpp+='''
void fits(Window&w,int i){auto&a=w.widget[i];assert(a.left>=0&&a.right<w.width&&a.top>=0&&a.bottom<w.height&&a.left<=a.right&&a.top<=a.bottom);}
template<class T>void roundtrip(int cls,int id){T w;w.window_class=cls;for(int n=0;n<20;n++)for(bool upper:{false,true,false}){w.OnN3DSScreenChange(upper);assert(w.width==(upper?400:320)&&w.height<=218&&w.left==(upper?0:40)&&w.top+w.height<=240);fits(w,id);}}
int main(){
 int valid[16]={0,2,3,4,5,6,7,9,10,11,12,13,14,15,16,17};for(int row=0;row<18;row++)for(int pixel=0;pixel<22;pixel++){int actual=N3DSDifficultyOption(row/6,(row%6)*22+pixel);assert(actual==(row<16?valid[row]:-1));}assert(N3DSDifficultyOption(-1,0)==-1&&N3DSDifficultyOption(0,-1)==-1&&N3DSDifficultyOption(0,132)==-1);
 roundtrip<Company>(WC_COMPANY,CW_WIDGET_COMPANY_NAME);roundtrip<Options>(WC_GAME_OPTIONS,GAMEOPT_FULLSCREEN);roundtrip<Settings>(WC_GAME_OPTIONS,SETTINGSEL_OPTIONSPANEL);roundtrip<Difficulty>(WC_GAME_OPTIONS,GDW_CANCEL);roundtrip<Funding>(WC_BUILD_INDUSTRY,DPIW_FUND_WIDGET);roundtrip<Industries>(WC_INDUSTRY_DIRECTORY,IDW_INDUSTRY_LIST);
 for(int cargo:{1,12,15,32}){Stations w;w.window_class=WC_STATION_LIST;w.widget_count=SLW_CARGOSTART+cargo;for(int n=0;n<20;n++)for(bool upper:{false,true,false}){w.OnN3DSScreenChange(upper);assert(w.vscroll.cap>=4);for(int i=0;i<cargo;i++){fits(w,SLW_CARGOSTART+i);auto&a=w.widget[SLW_CARGOSTART+i];assert(a.right-a.left==21&&a.bottom-a.top==21);}fits(w,SLW_LIST);assert(w.widget[SLW_LIST].bottom-w.widget[SLW_LIST].top+1==w.vscroll.cap*22);}}
 Title title;title.Layout();assert(title.height==240&&title.top==0);for(int i=2;i<=SGI_EXIT;i++){fits(title,i);if(i<SGI_TEMPERATE_LANDSCAPE||i>SGI_TOYLAND_LANDSCAPE)assert(title.widget[i].bottom-title.widget[i].top+1==22);for(int j=2;j<i;j++){auto&a=title.widget[i];auto&b=title.widget[j];assert(a.right<b.left||a.left>b.right||a.bottom<b.top||a.top>b.bottom);}}
 std::cout<<"management native bounds, 20 screen round trips, all 32 cargo filters, aligned row capacities and 22px main-menu targets passed\\n";
}
'''
cpp='#include \"'+str(root/'src/n3ds_menu_scroll.h')+'\"\n'+cpp
f=out/'management-layouts.cpp';f.write_text(cpp);exe=out/'management-layouts';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
