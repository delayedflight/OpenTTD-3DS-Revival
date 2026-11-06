"""Compile actual file-browser/news reflows and test native bounds and viewport centres."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
fios=(root/'src/misc_gui.cpp').read_text();news=(root/'src/news_gui.cpp').read_text();win=(root/'src/window.cpp').read_text();types=(root/'src/window_type.h').read_text()
def block(s,mark):
 a=s.index(mark);i=s.index('{',a)+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
a=types.index('enum WindowClass');z=types.index('};',a)+2
cpp='''#define N3DS 1
#include <algorithm>
#include <cassert>
#include <iostream>
#include <cmath>
#include "SCROLL_HEADER"
using std::min;using std::max;using uint=unsigned;
template<class T>T Clamp(T a,T l,T h){return min(max(a,l),h);}
'''.replace('SCROLL_HEADER',str(root/'src/n3ds_menu_scroll.h'))+types[a:z]+'''
enum{GM_MENU,GM_NORMAL,GM_EDITOR};int _game_mode=GM_NORMAL;enum{SLD_LOAD_GAME,SLD_LOAD_SCENARIO,SLD_SAVE_GAME,SLD_SAVE_SCENARIO,SLD_LOAD_HEIGHTMAP};int _saveload_mode=0;
enum NewsMode{NM_NORMAL,NM_THIN,NM_SMALL};struct{NewsMode display_mode;} _news_subtype_data[]={{NM_NORMAL},{NM_THIN},{NM_SMALL}};struct NewsItem{int subtype=0;};
enum{WWT_CAPTION,WWT_STICKYBOX};const int STR_NULL=0;
struct Window;bool N3DSUsesScrollableWorkspace(const Window*){return false;}bool N3DSIsConstructionWindow(WindowClass){return false;}bool N3DSIsManagementWindow(WindowClass){return false;}
struct Widget{int type=-1,left=0,right=0,top=0,bottom=0,tooltips=0;bool hidden=false;};struct Point{int x,y;};
struct ViewportData{int left=3,top=17,width=426,height=110,zoom=2,virtual_width=1704,virtual_height=440,virtual_left=200,virtual_top=300,scrollpos_x=200,scrollpos_y=300,dest_scrollpos_x=200,dest_scrollpos_y=300;};
int ScaleByZoom(int n,int zoom){return n<<zoom;}void MarkWholeScreenDirty(){}
struct Window{bool n3ds_train_depot=false,n3ds_train_depot_top=false,n3ds_user_position=false,n3ds_position_upper=false;int n3ds_user_left=0,n3ds_user_top=22;bool n3ds_native_layout=false;int n3ds_canvas_x=0,n3ds_canvas_y=0,left=0,top=0,width=257,height=154,widget_count=20;WindowClass window_class=WC_SAVELOAD;Widget widget[24];ViewportData*viewport=nullptr;struct{int cap=0;}vscroll;struct{int step_width=1,width=257;}resize;
void OnN3DSScreenChange(bool);void OnResize(Point,Point){};void HideWidget(int i){widget[i].hidden=true;}void SetWidgetHiddenState(int i,bool b){widget[i].hidden=b;}};
void ResizeWindow(Window*w,int dx,int dy){w->width+=dx;w->height+=dy;}
'''+block(win,'void N3DSWidgetRect')+'\n'+block(win,'void Window::OnN3DSScreenChange')+'\nstruct Files:Window{'+block(fios[fios.index('struct SaveLoadWindow'):],'enum SaveLoadWindowWidgets')+';'+block(fios[fios.index('struct SaveLoadWindow'):],'virtual void OnN3DSScreenChange(bool upper)')+'};\nstruct Paper:Window{NewsItem*ni;'+block(news[news.index('struct NewsWindow'):],'virtual void OnN3DSScreenChange(bool upper)')+'''};
void fits(Window&w,int id){auto&r=w.widget[id];assert(r.left>=0&&r.right<w.width&&r.top>=0&&r.bottom<w.height&&r.left<=r.right&&r.top<=r.bottom);}
int main(){
 for(int mode=0;mode<=4;mode++)for(int game:{GM_MENU,GM_NORMAL,GM_EDITOR}){_saveload_mode=mode;_game_mode=game;Files w;for(int n=0;n<20;n++)for(bool upper:{false,true,false}){w.OnN3DSScreenChange(upper);assert(w.width==(upper?400:320)&&w.height==218&&w.n3ds_native_layout);assert(w.left==(upper?0:40)&&w.top+w.height<=240);int rows=mode==SLD_SAVE_GAME||mode==SLD_SAVE_SCENARIO?5:(mode==SLD_LOAD_GAME?7:6);assert(w.vscroll.cap==rows);fits(w,7);fits(w,8);fits(w,6);assert(w.widget[7].bottom-w.widget[7].top+1==rows*22);assert(w.widget[2].bottom-w.widget[2].top+1==22);if(mode==SLD_SAVE_GAME||mode==SLD_SAVE_SCENARIO){fits(w,10);fits(w,11);fits(w,12);assert(w.widget[10].bottom-w.widget[10].top+1==22);}else if(mode!=SLD_LOAD_GAME){fits(w,9);assert(!w.widget[9].hidden);}}}
 _game_mode=GM_NORMAL;for(int mode=0;mode<3;mode++)for(bool camera:{false,true}){Paper p;NewsItem item;item.subtype=mode;p.ni=&item;ViewportData vp;if(camera)p.viewport=&vp;int cx=vp.scrollpos_x+vp.virtual_width/2,cy=vp.scrollpos_y+vp.virtual_height/2;for(int n=0;n<20;n++)for(bool upper:{false,true,false}){p.OnN3DSScreenChange(upper);assert(p.width==(upper?400:320)&&p.height<=218&&p.n3ds_native_layout);fits(p,0);fits(p,1);if(mode==NM_SMALL)fits(p,3);assert(p.left==(upper?0:40)&&p.top+p.height<=240);if(camera){assert(vp.left==p.left+2&&vp.top>=p.top&&vp.top+vp.height<=p.top+p.height);assert(vp.width==p.width-4);assert(std::abs(vp.scrollpos_x+vp.virtual_width/2-cx)<=1&&std::abs(vp.scrollpos_y+vp.virtual_height/2-cy)<=1);}}}
 std::cout<<"all five file modes in title/game contexts, larger targets/row capacities, all news styles and 20 viewport-centred screen round trips passed\\n";
}
'''
f=out/'file-news-layouts.cpp';f.write_text(cpp);exe=out/'file-news-layouts';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
