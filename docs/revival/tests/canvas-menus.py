"""Compile actual menu routing, anchoring, scrollbar gestures and town layout."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
v=(root/'src/video/sdl_v.cpp').read_text();win=(root/'src/window.cpp').read_text();types=(root/'src/window_type.h').read_text();town=(root/'src/town_gui.cpp').read_text();news=(root/'src/news_gui.cpp').read_text()
def block(s,mark):
 a=s.index(mark);i=s.index('{',a)+1;d=1
 while d:d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
enum_start=types.index('enum WindowClass');enum_end=types.index('};',enum_start)+2
town_part=town[town.index('struct TownDirectoryWindow'):]
cpp='''#define N3DS 1
#include <algorithm>
#include <cassert>
#include <iostream>
#include <vector>
#include "SCROLL_HEADER"
using std::min;using std::max;using uint=unsigned;using WindowNumber=int;using byte=unsigned char;
template<class T>T Clamp(T a,T l,T h){return min(max(a,l),h);}
'''.replace('SCROLL_HEADER',str(root/'src/n3ds_menu_scroll.h'))+types[enum_start:enum_end]+'\n'+'\n'.join(block(v,m) for m in ['bool N3DSIsMapConstructionWindow','bool N3DSIsConstructionWindow','bool N3DSIsManagementWindow','bool N3DSIsCanvasWindow','bool N3DSUsesScreenPin'])+'''
const int GM_EDITOR=2,GM_NORMAL=1,GM_MENU=0,WWT_CAPTION=1,WWT_STICKYBOX=2,STR_NULL=0,COLOUR_GREY=0,FR_NONE=0,FR_LOWERED=1,TC_WHITE=0,ZOOM_LVL_NORMAL=0;
int _game_mode=GM_NORMAL;bool _upper_ui=false,_map_pad=false,_touch_held=false,_pad_held=false,_left_button_down=false,_panel_needs_draw=false;
struct Point{int x,y;};struct Viewport{int left=43,top=39;};struct Widget{int type=0,left=0,right=0,top=0,bottom=0,tooltips=0;};
struct Window{bool n3ds_train_depot=false,n3ds_train_depot_top=false,n3ds_user_position=false,n3ds_position_upper=false;int n3ds_user_left=0,n3ds_user_top=22;bool n3ds_native_layout=false;WindowClass window_class=WC_FINANCES;int window_number=7,left=40,top=22,width=640,height=400,n3ds_canvas_x=0,n3ds_canvas_y=0,widget_count=0;Viewport*viewport=nullptr;Widget widget[20];struct{int step_width=1,width=36;}resize;struct{int cap=0;}vscroll;void HideWidget(int){};void OnResize(Point,Point){};void SetWidgetHiddenState(int,bool){};void OnN3DSScreenChange(bool);Window*z_back=nullptr;}menu;
Window*front=&menu;Window*N3DSFrontUi(){return front;}void MarkWholeScreenDirty(){};void ResizeWindow(Window*w,int dx,int dy){w->width+=dx;w->height+=dy;}
'''+block(v,'bool N3DSUsesScrollableWorkspace')+'\n'+block(win,'void N3DSWidgetRect')+'\n'+block(win,'void Window::OnN3DSScreenChange')+'''
static bool _canvas_touch=false,_canvas_pending=false;static WindowClass _canvas_class;static WindowNumber _canvas_number;
static int _canvas_target_x,_canvas_target_y,_canvas_drag_axis=0,_canvas_grab=0;
'''+ '\n'.join(block(v,m) for m in ['static Window *N3DSCanvasFront()','static bool N3DSCanvasOverflow','static N3DSMenuScrollBar N3DSCanvasBar','static bool N3DSCanvasFooterClick','static void MoveN3DSCanvasDrag','static void ProcessN3DSCanvasMove'])+'''
#define FOR_ALL_WINDOWS_FROM_FRONT(w) for(w=front;w!=nullptr;w=w->z_back)
'''+block(v,'static bool NativeN3DSOrdersRow')+'''
struct DrawPixelInfo{void*dst_ptr;int width,height,left,top,zoom;}_screen,*_cur_dpi;
struct Format{int BytesPerPixel;};struct Surface{void*pixels;int pitch;Format*format;}*_sdl_screen;
int frames=0;void DrawFrameRect(int l,int t,int r,int b,int,int){assert(l>=0&&r<320&&t>=0&&b<240&&l<=r&&t<=b);frames++;}
void DoDrawStringCentered(int x,int y,const char*,int){assert(x>=0&&x<320&&y>=0&&y<240);}
'''+block(v,'static void DrawN3DSCanvasFooter')+'''
struct Town:Window{'''+block(town_part,'enum TownDirectoryWidget')+';'+block(town_part,'virtual void OnN3DSScreenChange(bool upper)')+'''};
'''+'''int Delta(int a,int b){return a>b?a-b:b-a;}void SetDirtyBlocks(int,int,int,int){};struct News:Window{int chat_height=0;'''+block(news[news.index('struct NewsWindow'):],'virtual void OnTick()')+'};'+'''
void release(){_canvas_touch=_touch_held=false;_canvas_drag_axis=0;ProcessN3DSCanvasMove();}
int main(){
 News paper;paper.window_class=WC_NEWS_WINDOW;paper.top=-40;paper.OnTick();assert(paper.top==-40);
 Town town;town.window_class=WC_TOWN_DIRECTORY;for(int n=0;n<20;n++)for(bool upper:{false,true,false}){town.OnN3DSScreenChange(upper);assert(town.width==(upper?400:320)&&town.height==190&&town.vscroll.cap==6);assert(town.widget[Town::TDW_CENTERTOWN].bottom-town.widget[Town::TDW_CENTERTOWN].top+1==6*22);assert(town.widget[2].right==town.width-1);}
 menu.widget_count=2;menu.widget[0].type=WWT_CAPTION;menu.widget[0].right=399;menu.widget[1].type=WWT_STICKYBOX;menu.widget[1].left=388;menu.widget[1].right=399;menu.width=275;menu.OnN3DSScreenChange(false);assert(menu.widget[1].right==274&&menu.widget[0].right==262);menu.widget_count=0;
 menu.window_class=WC_GAME_OPTIONS;assert(N3DSUsesScrollableWorkspace(&menu));menu.n3ds_native_layout=true;assert(!N3DSUsesScrollableWorkspace(&menu));menu.n3ds_native_layout=false;menu.window_class=WC_FINANCES;
 int canvas=0;for(int c=1;c<=WC_AI_SETTINGS;c++){auto cls=(WindowClass)c;if(N3DSIsCanvasWindow(cls)){canvas++;assert(N3DSUsesScreenPin(cls));}}
 for(auto cls:{WC_FINANCES,WC_COMPANY_COLOUR,WC_COMPANY_MANAGER_FACE,WC_TOWN_DIRECTORY,WC_TOWN_VIEW,WC_TOWN_AUTHORITY,WC_SMALLMAP,WC_EXTRA_VIEW_PORT,WC_INCOME_GRAPH,WC_OPERATING_PROFIT,WC_DELIVERED_CARGO,WC_PERFORMANCE_HISTORY,WC_COMPANY_VALUE,WC_PAYMENT_RATES,WC_COMPANY_LEAGUE,WC_PERFORMANCE_DETAIL,WC_GRAPH_LEGEND,WC_SUBSIDIES_LIST,WC_MESSAGE_HISTORY,WC_NEWS_WINDOW,WC_MUSIC_WINDOW,WC_MUSIC_TRACK_SELECTION,WC_VEHICLE_REFIT,WC_VEHICLE_TIMETABLE,WC_REPLACE_VEHICLE,WC_WAYPOINT_VIEW,WC_SIGN_LIST,WC_SAVELOAD,WC_QUERY_STRING,WC_CONFIRM_POPUP_QUERY,WC_TRANSPARENCY_TOOLBAR,WC_AI_DEBUG,WC_AI_LIST,WC_AI_SETTINGS})assert(N3DSIsCanvasWindow(cls));
 Viewport vp;menu.viewport=&vp;
 for(int width:{180,320,400,407,640,900})for(int height:{60,196,198,220,400})for(bool upper:{false,true,false})for(int pan:{-100,0,40,10000}){
  menu.width=width;menu.height=height;_upper_ui=upper;menu.n3ds_canvas_x=menu.n3ds_canvas_y=pan;int oldx=menu.left,oldy=menu.top,vpx=vp.left,vpy=vp.top;int view=N3DSMenuScrollBar::ViewWidth(height,upper);
  menu.OnN3DSScreenChange(upper);assert(menu.n3ds_canvas_x>=0&&menu.n3ds_canvas_x<=max(0,width-view));assert(menu.n3ds_canvas_y>=0&&menu.n3ds_canvas_y<=max(0,height-196));assert(vp.left-vpx==menu.left-oldx&&vp.top-vpy==menu.top-oldy);assert(menu.left==((upper?0:40)+max(0,(view-width)/2)-menu.n3ds_canvas_x));assert(menu.top==22-menu.n3ds_canvas_y);
 }
 _upper_ui=false;menu.width=640;menu.height=400;menu.n3ds_canvas_x=menu.n3ds_canvas_y=0;menu.OnN3DSScreenChange(false);assert(NativeN3DSOrdersRow(22)&&NativeN3DSOrdersRow(217));
 assert(!N3DSCanvasFooterClick(320,239)&&!N3DSCanvasFooterClick(0,217));
 assert(N3DSCanvasFooterClick(309,239));ProcessN3DSCanvasMove();assert(menu.n3ds_canvas_x==0);release();assert(menu.n3ds_canvas_x==64);ProcessN3DSCanvasMove();assert(menu.n3ds_canvas_x==64);
 assert(N3DSCanvasFooterClick(309,207));release();assert(menu.n3ds_canvas_y==48);
 assert(N3DSCanvasFooterClick(22,225));release();assert(menu.n3ds_canvas_x==0&&menu.n3ds_canvas_y==0);
 auto h=N3DSCanvasBar(&menu,false);assert(N3DSCanvasFooterClick(h.ThumbStart()+10,225));MoveN3DSCanvasDrag(297,225);ProcessN3DSCanvasMove();assert(_touch_held&&menu.n3ds_canvas_x==342&&!_left_button_down);MoveN3DSCanvasDrag(h.TrackStart()+10,225);ProcessN3DSCanvasMove();assert(menu.n3ds_canvas_x==0);release();
 auto vertical=N3DSCanvasBar(&menu,true);assert(N3DSCanvasFooterClick(309,vertical.ThumbStart()+10));MoveN3DSCanvasDrag(309,195);ProcessN3DSCanvasMove();assert(menu.n3ds_canvas_y==204);release();
 assert(N3DSCanvasFooterClick(22,225));release();assert(N3DSCanvasFooterClick(297,225));release();assert(menu.n3ds_canvas_x==298);
 assert(N3DSCanvasFooterClick(22,225));release();assert(N3DSCanvasFooterClick(309,225));front=nullptr;release();assert(menu.n3ds_canvas_x==0);front=&menu;
 assert(N3DSCanvasFooterClick(309,225));menu.window_class=WC_SAVELOAD;release();assert(menu.n3ds_canvas_x==0);menu.window_class=WC_FINANCES;
 _map_pad=true;assert(!N3DSCanvasFooterClick(309,225));_map_pad=false;_game_mode=GM_MENU;assert(!N3DSCanvasFooterClick(309,225));_game_mode=GM_NORMAL;_pad_held=true;assert(!N3DSCanvasFooterClick(309,225));_pad_held=false;
 std::vector<byte>buf(400*480*4);Format format{1};Surface surface{buf.data(),400,&format};_sdl_screen=&surface;DrawPixelInfo dpi{};_cur_dpi=&dpi;for(int w:{200,320,400,900})for(int height:{100,196,198,400}){menu.width=w;menu.height=height;menu.OnN3DSScreenChange(false);DrawN3DSCanvasFooter();assert(_cur_dpi==&dpi);}assert(frames>0);
 menu.width=200;menu.height=100;assert(!N3DSCanvasOverflow(&menu));
 std::cout<<canvas<<" dialog routes, 360 pan/viewport cases, live thumb dragging, arrows/page clicks, release/target/mode guards, scrollbar drawing bounds, dynamic pins and native town rows passed\\n";
}
'''
f=out/'canvas-menus.cpp';f.write_text(cpp);exe=out/'canvas-menus';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
