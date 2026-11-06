"""Exercise actual native dropdown layout and hit testing with list/window stubs."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[3];s=(root/'src/widgets/dropdown.cpp').read_text();out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
a=s.index('#ifdef N3DS\n\t/* A full native-width popup');z=s.index('#else',a);layout=s[a:z]
a=s.index('\tbool GetDropDownItem(int &value)');i=s.index('{',a)+1;d=1
while d:
 d+=(s[i]=='{')-(s[i]=='}');i+=1
hit=s[a:i]
cpp=r'''#define N3DS 1
#include <algorithm>
#include <cassert>
#include <list>
#include <iostream>
using std::min;using std::max;using uint=unsigned;
struct DropDownListItem {int result,h=10;bool masked=false,select=true;uint Height(uint)const{return h;}bool Selectable()const{return select;}};
using DropDownList=std::list<DropDownListItem*>;
struct Layout{int x,y,w,h,row,cap;bool scroll;};
Layout MakeLayout(DropDownList *list,uint width){
'''+layout.replace('#ifdef N3DS','')+r'''
 return {left,top,(int)width,height+4,row_height,rows,scroll};}
struct {struct{int x,y;}pos;} _cursor;
struct Widget{int right;};
struct Window{int left,top,width,height,row_height;Widget widget[2];struct{int pos=0;}vscroll;DropDownList *list;bool GetDropDownItem(int &value);};
int GetWidgetFromPos(Window*w,int x,int y){if(x<0||x>=w->width||y<0||y>=w->height)return -1;return x>w->widget[0].right?1:0;}
'''+hit.replace('bool GetDropDownItem','bool Window::GetDropDownItem')+r'''
int main(){
 DropDownList l;DropDownListItem items[100];for(int i=0;i<100;i++){items[i].result=i;l.push_back(&items[i]);}
 Layout g=MakeLayout(&l,15);assert(g.x==40&&g.w==320&&g.y==22&&g.row==22&&g.cap==9&&g.h==202&&g.scroll);
 Window w{g.x,g.y,g.w,g.h,g.row,{{299},{319}},{},&l};int value=-1;
 for(int pos:{0,47,91}){w.vscroll.pos=pos;for(int row=0;row<g.cap;row++){
  _cursor.pos={42,g.y+2+row*g.row+11};assert(w.GetDropDownItem(value)&&value==pos+row);
 }}
 _cursor.pos={350,g.y+5};assert(!w.GetDropDownItem(value)); // Scrollbar cannot choose a row.
 w.vscroll.pos=0;_cursor.pos={42,g.y+5};items[0].masked=true;assert(!w.GetDropDownItem(value));items[0].masked=false;items[0].select=false;assert(!w.GetDropDownItem(value));items[0].select=true;
 items[1].h=26;g=MakeLayout(&l,400);assert(g.row==26&&g.cap==8&&g.h==212&&g.y+g.h<=240);
 DropDownList shortlist{&items[0],&items[2]};g=MakeLayout(&shortlist,400);assert(g.cap==2&&g.h==48&&!g.scroll);
 std::cout<<"native width, short/long/sprite lists, scrolling, masked/separator rows and scrollbar hit exclusion passed\n";
}
'''
f=out/'touch-dropdown.cpp';f.write_text(cpp);exe=out/'touch-dropdown'
subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
