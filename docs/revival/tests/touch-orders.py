"""Run the actual Orders widget reflow on all three legacy widget tables."""
from pathlib import Path
import re,subprocess,sys
root=Path(__file__).resolve().parents[3];s=(root/'src/order_gui.cpp').read_text();out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
a=s.index('OrdersWindow(const WindowDesc');a=s.index('#ifdef N3DS',a);z=s.index('#endif',a);code=s[a:z].replace('#ifdef N3DS','')
tables=[];names=[]
for table in ['_orders_train_widgets','_orders_widgets','_other_orders_widgets']:
 a=s.index('static const Widget '+table);z=s.index('\n};',a);rows=[]
 for line in s[a:z].splitlines():
  m=re.search(r'\{\s*(WWT_\w+),\s*\w+,\s*\w+,\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),.*// (ORDER_WIDGET_\w+)',line)
  if m:
   kind,l,r,t,b,name=m.groups();rows.append('{'+','.join([l,r,t,b,'0' if kind=='WWT_EMPTY' else '1'])+'}');
   if name not in names:names.append(name)
 tables.append(rows)
cpp='''#include <cassert>\n#include <iostream>\nconst int WWT_EMPTY=0;\n'''+ 'enum{'+','.join(names)+'};\n'+'''struct Widget{int left,right,top,bottom,type;};struct Pane{int widget_count=25;Widget widget[25];void Reflow(){'''+code+'''}};
int main(){
'''
for rows in tables:
 assert len(rows)==25
 cpp+='''{Pane p{25,{'''+','.join(rows)+'''}};p.Reflow();
 for(auto &w:p.widget)if(w.type){assert(w.left>=0&&w.right<320&&w.left<=w.right);assert(w.top>=0&&w.bottom<192&&w.top<=w.bottom);}
 assert((p.widget[ORDER_WIDGET_ORDER_LIST].bottom-p.widget[ORDER_WIDGET_ORDER_LIST].top)/22==6);
 assert(p.widget[ORDER_WIDGET_RESIZE].type==WWT_EMPTY);
 for(int i=0;i<6;i++)assert((15+22*i-p.widget[ORDER_WIDGET_ORDER_LIST].top-1)/22==i);
}\n'''
cpp+='std::cout<<"train/road, ship/aircraft and competitor Orders: widget bounds, six 22-pixel rows and fixed pane passed\\n";}\n'
f=out/'touch-orders.cpp';f.write_text(cpp);exe=out/'touch-orders';subprocess.run(['clang++','-std=c++14','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
