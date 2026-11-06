"""Compile actual screen-change callbacks; verify both layouts and round trips."""
from pathlib import Path
import re,subprocess,sys
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
g=(root/'src/group_gui.cpp').read_text();v=(root/'src/vehicle_gui.cpp').read_text();w=(root/'src/window.cpp').read_text()
def body(s,mark,start=0):
 a=s.index(mark,start);i=s.index('{',a)+1;d=1
 while d:
  d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
def table(s,name):
 a=s.index('static const Widget '+name);z=s.index('\n};',a);rows=[]
 for line in s[a:z].splitlines():
  m=re.search(r'\{\s*(WWT_\w+),\s*(RESIZE_\w+),\s*\w+,\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),',line)
  if m:
   kind,flag,l,r,t,b=m.groups();rows.append('{'+','.join([l,r,t,b,flag,kind,'0'])+'}')
 return rows
def enum(s,mark):return body(s,mark)+';\n'
def fragment(s,mark):
 a=s.index(mark);return s[a:s.index('#endif',a)]
grows=table(g,'_group_widgets');vrows=table(v,'_vehicle_details_widgets');lrows=table(v,'_vehicle_list_widgets')
alltypes=set(re.findall(r'\bWWT_\w+',g+v));alltypes.discard('WWT_EMPTY');alltypes.discard('WWT_LAST')
cpp=r'''#define N3DS 1
#include <cassert>
#include <iostream>
#include <cstring>
using byte=unsigned char;using WidgetType=int;using int16=short;using uint=unsigned;
#define GB(v,a,b) (((v)>>(a))&((1<<(b))-1))
const int RESIZE_NONE=0,RESIZE_LEFT=1,RESIZE_RIGHT=2,RESIZE_TOP=4,RESIZE_BOTTOM=8,RESIZE_LR=3,RESIZE_RB=10,RESIZE_RTB=14,RESIZE_LRB=11,RESIZE_TB=12,RESIZE_LRTB=15,RESIZE_LRT=7;
const int VEH_TRAIN=0,VEH_ROAD=1,VEH_SHIP=2,VEH_AIRCRAFT=3,STR_SORT_BY=1,STR_EMPTY=0;
struct Vehicle{int type;}veh;const Vehicle*GetVehicle(int){return &veh;}void MarkWholeScreenDirty(){}
struct Widget{int left,right,top,bottom,display_flags,type,data;};struct N3DSWidgetLayout{int16 left,right,top,bottom;byte type;};
struct Base{Widget widget[40];bool hidden[40]={},disabled[40]={};int width=400,height=113,left=0,top=22,widget_count,vehicle_type=0,window_number=0;struct{int cap=6,pos=0;}vscroll,vscroll2;struct{int height=0,step_height=26;}resize;void SetWidgetHiddenState(int i,bool b){hidden[i]=b;}void SetWidgetDisabledState(int i,bool b){disabled[i]=b;}void SetDirty(){};};using Window=Base;
'''
cpp+='enum{WWT_EMPTY=0,'+','.join(sorted(alltypes))+',WWT_LAST=255};\n'
cpp+=enum(g,'enum GroupListWidgets')+enum(v,'enum VehicleListWidgets')+enum(v,'enum VehicleDetailsWindowWidgets') if 'enum VehicleListWidgets' in v else ''
# The old list enum has a descriptive alternate name in some upstream snapshots.
if 'enum GroupListWidgets' not in cpp:
 cpp+=enum(g,'enum GroupListWidgets')
 a=v.index('VLW_WIDGET_CLOSEBOX');a=v.rfind('enum ',0,a);cpp+=body(v,v[a:v.index('{',a)])+';\n'
 cpp+=enum(v,'enum VehicleDetailsWindowWidgets')
cpp+=body(w,'void ResizeWindow(Window *w, int x, int y)')+'\n'
for name,s,start,fields in [('Group',g,g.index('class VehicleGroupWindow'),'''N3DSWidgetLayout n3ds_layout[25];bool n3ds_ready=true,n3ds_compact=false,n3ds_groups=false;'''),('Details',v,v.index('struct VehicleDetailsWindow'),'''N3DSWidgetLayout n3ds_layout[17];bool n3ds_ready=true,n3ds_compact=false,n3ds_overview=true;int n3ds_height,n3ds_cap;'''),('Simple',v,v.index('struct VehicleListWindow'),'''N3DSWidgetLayout n3ds_layout[15];bool n3ds_ready=true;int n3ds_width,n3ds_height,n3ds_cap;''')]:
 cpp+='struct '+name+':Base{'+fields+body(s,'void N3DSRect(',start)+'\n'+body(s,'virtual void OnN3DSScreenChange(bool upper)',start)+'\n'
 if name=='Details':cpp+=body(s,'void N3DSVisibility(const Vehicle *v)',start)+'\n'
 cpp+='void Save(){for(uint i=0;i<this->widget_count;i++){auto&w=this->widget[i];auto&a=this->n3ds_layout[i];a.left=w.left;a.right=w.right;a.top=w.top;a.bottom=w.bottom;a.type=w.type;}}};\n'
cpp+='''void Bounds(const Base&p){for(int i=0;i<p.widget_count;i++){auto&w=p.widget[i];if(p.hidden[i]||w.type==WWT_EMPTY||w.right<w.left)continue;assert(w.left>=0&&w.right<p.width&&w.top>=0&&w.bottom<p.height);}}
int main(){
'''
cpp+='Widget gs[]={'+','.join(grows)+',{0,0,0,0,0,WWT_LAST,0}};Widget ds[]={'+','.join(vrows)+',{0,0,0,0,0,WWT_LAST,0}};Widget ls[]={'+','.join(lrows)+',{0,0,0,0,0,WWT_LAST,0}};\n'
cpp+='''for(int type=0;type<4;type++){
 Group p;p.widget_count=25;p.vehicle_type=type;p.resize.step_height=type<2?26:39;for(int i=0;i<=25;i++)p.widget[i]=gs[i];
'''+fragment(g,'  /* Narrow only')+fragment(g,'\t\t/* A taller action row')+'''
 p.Save();for(int turn=0;turn<20;turn++){
  p.n3ds_groups=false;p.OnN3DSScreenChange(false);Bounds(p);assert(p.width==320&&p.left==40);assert(p.widget[GRP_WIDGET_LIST_VEHICLE].bottom-p.widget[GRP_WIDGET_LIST_VEHICLE].top+1==p.vscroll.cap*p.resize.step_height);
  p.n3ds_groups=true;p.OnN3DSScreenChange(false);Bounds(p);assert(p.widget[GRP_WIDGET_LIST_GROUP].bottom-p.widget[GRP_WIDGET_LIST_GROUP].top+1==p.vscroll2.cap*22);
  p.OnN3DSScreenChange(true);Bounds(p);for(int i=0;i<25;i++){auto&a=p.n3ds_layout[i];auto&w=p.widget[i];assert(w.left==a.left&&w.right==a.right&&w.top==a.top&&w.bottom==a.bottom);}
 }
 Details q;q.widget_count=17;for(int i=0;i<=17;i++)q.widget[i]=ds[i];veh.type=type;const Vehicle*v=&veh;
'''+fragment(v,'  /* Recover the five pixels')+'''
 if(type==0){ResizeWindow(&q,0,39);q.height+=12;q.vscroll.cap=6;}else if(type==3)ResizeWindow(&q,0,11);
 if(type!=0){q.vscroll.cap=1;q.widget[VLD_WIDGET_MIDDLE_DETAILS].right+=12;}
'''+fragment(v,'\t\t/* Increase service controls').replace('this->','q.')+'''
 q.n3ds_height=q.height;q.n3ds_cap=q.vscroll.cap;q.Save();
 for(int turn=0;turn<20;turn++){
  for(bool overview:{false,true}){q.n3ds_overview=overview;q.OnN3DSScreenChange(false);q.N3DSVisibility(v);Bounds(q);assert(q.width==320&&q.height==192);}
  q.OnN3DSScreenChange(true);q.N3DSVisibility(v);Bounds(q);assert(q.height==q.n3ds_height&&q.width==400);for(int i=0;i<17;i++){auto&a=q.n3ds_layout[i];auto&w=q.widget[i];assert(w.left==a.left&&w.right==a.right&&w.top==a.top&&w.bottom==a.bottom);}
 }
 Simple r;r.widget_count=15;r.vehicle_type=type;r.resize.step_height=type<2?26:39;r.width=260;r.height=194;for(int i=0;i<=15;i++)r.widget[i]=ls[i];if(type==0)ResizeWindow(&r,65,0);r.n3ds_width=r.width;r.n3ds_height=r.height;r.n3ds_cap=type<2?6:4;r.Save();r.OnN3DSScreenChange(false);Bounds(r);assert(r.width==320);r.OnN3DSScreenChange(true);Bounds(r);
}
std::cout<<"all four vehicle types: native pane bounds, group/vehicle pages, overview/details pages, exact row hit geometry and 20 reversible screen-switch round trips passed\\n";}
'''
# Initial transform snippets refer to the group/detail instance as 'this'.
cpp=cpp.replace('this->widget_count','this->widget_count')
# Only the setup in main has this-> references; substitute those for the relevant test object.
a=cpp.index('int main()');head=cpp[:a];tail=cpp[a:];a=tail.index('Details q;');tail=tail[:a].replace('this->','p.')+tail[a:].replace('this->','q.');cpp=head+tail
f=out/'compact-vehicles.cpp';f.write_text(cpp);exe=out/'compact-vehicles';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
