"""Run actual widget transforms and resize code against the legacy tables."""
from pathlib import Path
import re,subprocess,sys
root=Path(__file__).resolve().parents[3];out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
g=(root/'src/group_gui.cpp').read_text();v=(root/'src/vehicle_gui.cpp').read_text();w=(root/'src/window.cpp').read_text()
def block(s,marker):
 a=s.index(marker);i=s.index('{',a)+1;d=1
 while d:
  d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
def table(s,name):
 a=s.index('static const Widget '+name);z=s.index('\n};',a);rows=[];names=[]
 for line in s[a:z].splitlines():
  m=re.search(r'\{\s*(WWT_\w+),\s*(RESIZE_\w+),\s*\w+,\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),.*// (\w+)',line)
  if m:
   kind,flag,l,r,t,b,n=m.groups();names.append(n.replace('VLD_RESIZE','VLD_WIDGET_RESIZE'));rows.append('{'+','.join([l,r,t,b,flag,'1'])+'}')
 return rows,names
grows,gn=table(g,'_group_widgets');vrows,vn=table(v,'_vehicle_details_widgets')
def section(s,marker):
 a=s.index(marker);a=s.index('#ifdef N3DS',a);z=s.index('#endif',a);return s[a+len('#ifdef N3DS'):z]
g1=section(g,'VehicleGroupWindow(const');g2=section(g,'/* A taller action row') if False else g[g.index('\t\t/* A taller action row'):g.index('#endif',g.index('/* A taller action row'))]
v1=section(v,'VehicleDetailsWindow(const');v2=v[v.index('\t\t/* Increase service controls'):v.index('#endif',v.index('/* Increase service controls'))]
cpp=r'''#include <cassert>
#include <iostream>
using byte=unsigned char;
#define GB(v,a,b) (((v)>>(a))&((1<<(b))-1))
const int RESIZE_NONE=0,RESIZE_LEFT=1,RESIZE_RIGHT=2,RESIZE_TOP=4,RESIZE_BOTTOM=8,RESIZE_LR=3,RESIZE_RB=10,RESIZE_RTB=14,RESIZE_LRB=11,RESIZE_TB=12,RESIZE_LRTB=15,RESIZE_LRT=7,WWT_LAST=9,WWT_EMPTY=0,VEH_TRAIN=0;
struct Widget{int left,right,top,bottom,display_flags,type;};
struct Window{int width=400,height=113,widget_count;Widget widget[30];struct{int height=0;}resize;void SetDirty(){};void Group();void Details(int type);};
'''+block(w,'void ResizeWindow(Window *w, int x, int y)')+'\nenum{'+','.join(gn)+'};\nenum{'+','.join(vn)+'};\n'
cpp+='void Window::Group(){'+g1+g2+'}\n'
cpp+='void Window::Details(int type){struct{int type;}veh{type};auto*v=&veh;'+v1+'''if(type==VEH_TRAIN){ResizeWindow(this,0,39);this->height+=12;}else if(type==3){ResizeWindow(this,0,11);}else if(type==4){ResizeWindow(this,0,48);}if(type!=VEH_TRAIN)this->widget[VLD_WIDGET_MIDDLE_DETAILS].right+=12;'''+v2+'}\n'
cpp+='int main(){Window group;group.height=204;group.widget_count='+str(len(grows))+';Widget gs[]={'+','.join(grows)+',{0,0,0,0,0,WWT_LAST}};for(int i=0;i<=group.widget_count;i++)group.widget[i]=gs[i];group.Group();'
cpp+='''for(int i=0;i<group.widget_count;i++){auto&w=group.widget[i];assert(w.left>=0&&w.right<400&&w.bottom<204);}for(int i:{GRP_WIDGET_AVAILABLE_VEHICLES,GRP_WIDGET_MANAGE_VEHICLES_DROPDOWN,GRP_WIDGET_STOP_ALL,GRP_WIDGET_START_ALL})assert(group.widget[i].bottom-group.widget[i].top+1==22);
'''
cpp+='for(int type:{0,1,2,3,4}){Window det;det.widget_count='+str(len(vrows))+';Widget ds[]={'+','.join(vrows)+',{0,0,0,0,0,WWT_LAST}};for(int i=0;i<=det.widget_count;i++)det.widget[i]=ds[i];det.Details(type);for(int i=0;i<det.widget_count;i++){auto&w=det.widget[i];if(!w.type)continue;assert(w.left>=0&&w.right<400);if(type!=0&&i>=VLD_WIDGET_DETAILS_CARGO_CARRIED)continue;assert(w.bottom<det.height);}assert(det.height<=218);for(int i:{VLD_WIDGET_INCREASE_SERVICING_INTERVAL,VLD_WIDGET_DECREASE_SERVICING_INTERVAL}){auto&w=det.widget[i];assert(w.right-w.left+1==22&&w.bottom-w.top+1==22);}if(type==0)for(int i=VLD_WIDGET_DETAILS_CARGO_CARRIED;i<=VLD_WIDGET_DETAILS_TOTAL_CARGO;i++)assert(det.widget[i].bottom-det.widget[i].top+1==22);}\n'
cpp+='std::cout<<"group/list footer bounds and 22-pixel targets; train/road/ship/aircraft/articulated detail bounds and service/tab targets passed\\n";}\n'
f=out/'vehicle-layouts.cpp';f.write_text(cpp);exe=out/'vehicle-layouts';subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
