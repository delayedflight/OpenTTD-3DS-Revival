"""Exercise deferred picker entry/exit with the actual video-driver functions."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[3]; out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
s=(root/'src/video/sdl_v.cpp').read_text()
def body(marker):
 a=s.index(marker);i=s.index('{',a)+1;d=1
 while d:
  d+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
cpp=r'''#include <cassert>
#include <iostream>
struct Buttons {void Reset(){}} _build_buttons;
bool _station_picker_active=false,_pad_held=false,_touch_held=false,_left_button_down=false,_left_button_clicked=false,_map_pad=false,_panel_needs_draw=false;
int _station_picker_request=0,_game_mode=1,GM_NORMAL=1,centres=0;bool map_input=false;void *_map_ui_front;
void HandleMouseEvents(){} void *N3DSFrontUi(){return (void*)1;} void SelectN3DSInput(bool b){map_input=b;} void CenterN3DSMapCursor(){centres++;} void MarkWholeScreenDirty(){}
'''
cpp+=body('void N3DSRequestStationPicker(bool begin)')+'\n'+body('static void ProcessN3DSStationPicker()')
cpp+=r'''
int main(){
 N3DSRequestStationPicker(false);assert(_station_picker_request==0);
 N3DSRequestStationPicker(true);assert(!_map_pad);ProcessN3DSStationPicker();assert(_map_pad&&map_input&&_station_picker_active);
 _pad_held=true;N3DSRequestStationPicker(false);ProcessN3DSStationPicker();assert(_map_pad&&_station_picker_request==2);
 _pad_held=false;ProcessN3DSStationPicker();assert(!_map_pad&&!map_input&&!_station_picker_active&&centres==1);
 N3DSRequestStationPicker(true);N3DSRequestStationPicker(false);ProcessN3DSStationPicker();assert(!_map_pad);
 _game_mode=0;N3DSRequestStationPicker(true);ProcessN3DSStationPicker();assert(!_map_pad);
 std::cout<<"deferred picker entry, release-before-return, cancellation and menu guard passed\n";
}
'''
f=out/'station-picker.cpp';f.write_text(cpp);exe=out/'station-picker'
subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(f),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
