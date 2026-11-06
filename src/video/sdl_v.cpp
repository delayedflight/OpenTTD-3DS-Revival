/* $Id$ */

/** @file sdl_v.cpp Implementation of the SDL video driver. */

#ifdef WITH_SDL

#include "../stdafx.h"
#include "../n3ds_bootlog.h"
#include "../n3ds_ui.h"
#include "../n3ds_menu_scroll.h"
#include "../n3ds_controls.h"
#include "../openttd.h"
#include "../gfx_func.h"
#include "../sdl.h"
#include "../variables.h"
#include "../rev.h"
#include "../blitter/factory.hpp"
#include "../network/network.h"
#include "../functions.h"
#include "sdl_v.h"
#include <SDL.h>
#ifdef N3DS
#include <3ds.h>
#include "../window_gui.h"
#include "../table/sprites.h"
#include "../window_func.h"
#include "../tilehighlight_func.h"
#endif

static FVideoDriver_SDL iFVideoDriver_SDL;

static SDL_Surface *_sdl_screen;
static bool _all_modes;

#ifdef N3DS
static SDL_Joystick *_3ds_joystick;
static int _panel_x, _panel_y;
static int _last_touch_x, _last_touch_y;
static bool _touch_held;
static bool _pad_held;
static N3DSBuildButtons _build_buttons;
static bool _map_pad;
static bool _depot_focus_active;
static bool _station_picker_active;
static int _station_picker_request; // 0 none, 1 enter, 2 return after button release
static bool _panel_needs_draw = true;
static SDL_Surface *_ui_surface;
void *_n3ds_ui_pixels;
bool _n3ds_map_input;
int _n3ds_scroll_factor = 10;
Point _n3ds_map_cursor = {200, 120};
static Point _ui_cursor = {200, 120};
static bool NativeN3DSTitle();
static bool _upper_ui;
bool N3DSUpperUiActive() { return _upper_ui; }
static WindowClass _upper_ui_class;
static WindowNumber _upper_ui_number;
static bool _upper_request_pending, _upper_request_value;
static WindowClass _upper_request_class;
static WindowNumber _upper_request_number;
static void SetN3DSUpperUi(bool upper, bool preserve_placement = false);
static void CheckN3DSUpperUi();
static void SelectN3DSInput(bool map);
static bool _cursor_in_menu;
static bool _cursor_native_title;

N3DSMapCursorScope::N3DSMapCursorScope() : saved(_cursor.pos), saved_surface(_screen.dst_ptr)
{
 if (_upper_ui) {
  _cursor.pos = _ui_cursor;
  _screen.dst_ptr = _n3ds_ui_pixels;
 } else if (_game_mode == GM_MENU) {
  if (_n3ds_map_input) SelectN3DSInput(false);
  const bool native = NativeN3DSTitle();
  if (!_cursor_in_menu || native != _cursor_native_title) {
   /* Preserve the physical touch position when title/dialog scaling changes. */
   _cursor.pos.x = max(0, min(399, native ? _panel_x + 40 : _panel_x * 400 / 320));
   _cursor.pos.y = max(0, min(239, _panel_y));
   _cursor.delta.x = _cursor.delta.y = 0;
   _ui_cursor = _cursor.pos;
   _cursor.dirty = true;
  }
  saved = _cursor.pos;
  _cursor_native_title = native;
  _screen.dst_ptr = _n3ds_ui_pixels;
 } else {
  _cursor.pos = _n3ds_map_cursor;
 }
 _cursor_in_menu = _game_mode == GM_MENU;
 /* A mode transition needs a redraw even if the cursor did not move. */
 if (_n3ds_cursor_surface != _screen.dst_ptr) _cursor.dirty = true;
}
N3DSMapCursorScope::~N3DSMapCursorScope()
{
 _cursor.pos = saved;
 _screen.dst_ptr = saved_surface;
 _cur_dpi = &_screen;
}

static void SelectN3DSInput(bool map)
{
	if (_n3ds_map_input == map) return;
	if (_n3ds_map_input) _n3ds_map_cursor = _cursor.pos;
	else _ui_cursor = _cursor.pos;
	_n3ds_map_input = map;
	_cursor.pos = map ? _n3ds_map_cursor : _ui_cursor;
	_cursor.delta.x = _cursor.delta.y = 0;
	_cursor.dirty = true;
	_cursor.in_window = true;
}

static void CenterN3DSMapCursor()
{
 const Window *bar = FindWindowById(WC_STATUS_BAR, 0);
 const int visible_height = bar != NULL ? bar->top : _screen.height;
 _n3ds_map_cursor.x = _screen.width / 2;
 _n3ds_map_cursor.y = visible_height / 2;
 if (_n3ds_map_input) _cursor.pos = _n3ds_map_cursor;
 _cursor.dirty = true;
}

static Window *N3DSFrontUi()
{
 Window *w;
 FOR_ALL_WINDOWS_FROM_FRONT(w) {
  if (!N3DSTopWindow(w) && w->window_class != WC_TOOLTIPS) return w;
 }
 return NULL;
}
static Window *_map_ui_front;
static Window *N3DSUpperTrainDepot()
{
 if(_upper_ui)return NULL;Window*w;FOR_ALL_WINDOWS_FROM_FRONT(w)if(w->n3ds_train_depot_top)return w;return NULL;
}
static bool N3DSDepotFocus(){return _depot_focus_active&&_map_pad&&N3DSUpperTrainDepot()!=NULL;}
static void SetN3DSDepotFocus(bool focus)
{
 if(_pad_held||_touch_held)ResetObjectToPlace();
 _build_buttons.Reset();_left_button_down=_left_button_clicked=_pad_held=_touch_held=false;
 HandleMouseEvents();_map_pad=focus;_depot_focus_active=focus;_map_ui_front=N3DSFrontUi();SelectN3DSInput(focus);
 CenterN3DSMapCursor();_panel_needs_draw=true;MarkWholeScreenDirty();
}
static bool ToggleN3DSDepotScreen(WindowClass cls,WindowNumber number)
{
 if(cls!=WC_VEHICLE_DEPOT&&cls!=WC_BUILD_VEHICLE)return false;
 Window*depot=FindWindowById(WC_VEHICLE_DEPOT,number);if(depot==NULL||!depot->n3ds_train_depot)return false;
 if(_upper_ui)SetN3DSUpperUi(false);
 bool top=!depot->n3ds_train_depot_top;Window*w;
 FOR_ALL_WINDOWS_FROM_FRONT(w)w->n3ds_train_depot_top=false;
 depot->n3ds_train_depot_top=top;
 FOR_ALL_WINDOWS_FROM_FRONT(w)w->OnN3DSScreenChange(false);
 SetN3DSDepotFocus(top&&FindWindowById(WC_BUILD_VEHICLE,number)==NULL);
 return true;
}


/** Transfer the existing UI surface; no extra framebuffer is allocated. */
static void SetN3DSUpperUi(bool upper, bool preserve_placement)
{
 if (_upper_ui == upper) return;
 if (upper && ((_game_mode != GM_NORMAL && _game_mode != GM_EDITOR) || _map_pad)) return;
 Window *front = N3DSFrontUi();
 if (upper && (front == NULL || front->window_class == WC_MAIN_TOOLBAR)) return;
 if (!preserve_placement && (_pad_held || _touch_held)) ResetObjectToPlace();
 _build_buttons.Reset();
 _left_button_down = _left_button_clicked = _pad_held = _touch_held = false;
 HandleMouseEvents();
 SelectN3DSInput(false);
 _upper_ui = upper;
 if(upper){Window*w;FOR_ALL_WINDOWS_FROM_FRONT(w)w->n3ds_train_depot_top=false;}
 Window *layout_window;
 FOR_ALL_WINDOWS_FROM_FRONT(layout_window) layout_window->OnN3DSScreenChange(upper);
 if (upper) {
  _upper_ui_class = front->window_class;
  _upper_ui_number = front->window_number;
  _ui_cursor = _cursor.pos;
 }
 _cursor.dirty = true;
 _panel_needs_draw = true;
 MarkWholeScreenDirty();
}

bool N3DSIsMapConstructionWindow(WindowClass cls)
{
 return cls==WC_BUILD_TOOLBAR||cls==WC_SCEN_BUILD_TOOLBAR||cls==WC_BUILD_STATION||cls==WC_BUS_STATION||cls==WC_TRUCK_STATION||cls==WC_BUILD_DEPOT||cls==WC_BUILD_SIGNAL||cls==WC_FOUND_TOWN||cls==WC_SCEN_LAND_GEN||cls==WC_BUILD_TREES||cls==WC_BUILD_INDUSTRY;
}
bool N3DSIsConstructionWindow(WindowClass cls)
{
 return N3DSIsMapConstructionWindow(cls)||cls==WC_BUILD_BRIDGE||cls==WC_BUILD_VEHICLE||cls==WC_VEHICLE_DEPOT||cls==WC_SELECT_STATION||cls==WC_BUILD_INDUSTRY;
}

bool N3DSIsManagementWindow(WindowClass cls)
{
 return cls==WC_COMPANY||cls==WC_GAME_OPTIONS||cls==WC_CUSTOM_CURRENCY||cls==WC_INDUSTRY_DIRECTORY||cls==WC_STATION_LIST||cls==WC_INDUSTRY_VIEW||cls==WC_STATION_VIEW;
}

/** Remaining gameplay dialogs share a native, pannable workspace. */
bool N3DSIsCanvasWindow(WindowClass cls)
{
 if(N3DSIsManagementWindow(cls)||N3DSIsConstructionWindow(cls))return false;
 switch(cls){
  case WC_MAIN_WINDOW:case WC_MAIN_TOOLBAR:case WC_STATUS_BAR:case WC_TOOLTIPS:
  case WC_DROPDOWN_MENU:case WC_TOOLBAR_MENU:case WC_SELECT_GAME:
  case WC_TRAINS_LIST:case WC_ROADVEH_LIST:case WC_SHIPS_LIST:case WC_AIRCRAFT_LIST:
  case WC_VEHICLE_VIEW:case WC_VEHICLE_DETAILS:case WC_VEHICLE_ORDERS:
  case WC_CONSOLE:case WC_SEND_NETWORK_MSG:case WC_GENERATE_LANDSCAPE:
  case WC_GENERATE_PROGRESS_WINDOW:case WC_SCEN_INDUSTRY:case WC_INVALID:
   return false;
  default:return cls>WC_NONE&&cls<WC_INVALID;
 }
}

/** Several unrelated dialogs share WC_GAME_OPTIONS: inspect the window's layout. */
bool N3DSUsesScrollableWorkspace(const Window *w)
{
 return (N3DSIsCanvasWindow(w->window_class)||N3DSIsManagementWindow(w->window_class))&&!w->n3ds_native_layout;
}

bool N3DSUsesScreenPin(WindowClass cls)
{
 return N3DSIsCanvasWindow(cls)||N3DSIsManagementWindow(cls)||N3DSIsConstructionWindow(cls)||cls==WC_TRAINS_LIST||cls==WC_ROADVEH_LIST||cls==WC_SHIPS_LIST||cls==WC_AIRCRAFT_LIST||cls==WC_VEHICLE_DETAILS||cls==WC_VEHICLE_ORDERS||cls==WC_VEHICLE_VIEW;
}

void N3DSRequestMenuScreenChange(WindowClass cls, WindowNumber number)
{
 if (!N3DSUsesScreenPin(cls) || (_game_mode != GM_NORMAL && _game_mode != GM_EDITOR)) return;
 _upper_request_class=cls; _upper_request_number=number;
 _upper_request_value=!_upper_ui; _upper_request_pending=true;
}

static void ProcessN3DSMenuScreenChange()
{
 if (!_upper_request_pending) return;
 if (_left_button_down || _touch_held || _pad_held) return;
 _upper_request_pending=false;
 if ((_game_mode == GM_NORMAL || _game_mode == GM_EDITOR) && FindWindowById(_upper_request_class,_upper_request_number)!=NULL && !ToggleN3DSDepotScreen(_upper_request_class,_upper_request_number)) SetN3DSUpperUi(_upper_request_value);
}

static void CheckN3DSUpperUi()
{
 if (!_upper_ui) return;
 if ((_game_mode != GM_NORMAL && _game_mode != GM_EDITOR) || FindWindowById(_upper_ui_class, _upper_ui_number) == NULL) SetN3DSUpperUi(false);
}

/** A fixed Orders pane uses native pixels while it is the foreground UI. */
static bool NativeN3DSOrdersRow(int y)
{
 Window *w;
 FOR_ALL_WINDOWS_FROM_FRONT(w) {
  if (w->window_class==WC_MAIN_WINDOW || w->window_class==WC_STATUS_BAR || w->n3ds_train_depot_top || w->window_class == WC_TOOLTIPS || w->window_class == WC_DROPDOWN_MENU) continue;
  if ((_game_mode == GM_NORMAL || _game_mode == GM_EDITOR) && N3DSUsesScrollableWorkspace(w)) {
   if(y>=w->top&&y<w->top+w->height)return true;
   continue;
  }
  if ((w->n3ds_native_layout||N3DSIsManagementWindow(w->window_class)||N3DSIsConstructionWindow(w->window_class)) && w->left >= 40 && w->left+w->width <= 360) {
   if (y >= w->top && y < w->top+w->height) return true;
   continue;
  }
  if (w->window_class == WC_VEHICLE_VIEW && w->left >= 40 && w->left+w->width <= 360) {
   if (y >= w->top && y < w->top + w->height) return true;
   continue;
  }
  if ((w->window_class == WC_VEHICLE_ORDERS || w->window_class == WC_VEHICLE_DETAILS || w->window_class == WC_TRAINS_LIST || w->window_class == WC_ROADVEH_LIST || w->window_class == WC_SHIPS_LIST || w->window_class == WC_AIRCRAFT_LIST) && w->left == 40 && w->width == 320) return y >= w->top && y < w->top + w->height;
  return false;
 }
 return false;
}

/** Full-width dropdowns use the same native pixel and touch mapping. */
static bool NativeN3DSDropdownRow(int y)
{
 const Window *w = FindWindowById(WC_DROPDOWN_MENU, 0);
 return w != NULL && w->left == 40 && w->width == 320 && y >= w->top && y < w->top + w->height;
}

/** The main icon row is copied at 1:1; the remaining desktop keeps its fit. */
static bool NativeN3DSToolbarRow(int y)
{
 if ((_game_mode != GM_NORMAL && _game_mode != GM_EDITOR)) return false;
 const Window *w = FindWindowById(WC_MAIN_TOOLBAR, 0);
 if (w == NULL || w->left != 40 || w->width != 320 || y < w->top || y >= w->top + w->height) return false;
 /* Large dialogs may cover the toolbar: keep their rows consistently fitted. */
 const Window *v;
 FOR_ALL_WINDOWS_FROM_FRONT(v) {
  if (v == w) break;
  if(v->n3ds_train_depot_top)continue;
  if (v->window_class == WC_MAIN_WINDOW || v->window_class == WC_STATUS_BAR) continue;
  if (y >= v->top && y < v->top + v->height && v->left < 360 && v->left + v->width > 40) return false;
 }
 return true;
}

static bool NativeN3DSTitle()
{
 Window *w = N3DSFrontUi();
 return _game_mode == GM_MENU && w != NULL && (w->window_class == WC_SELECT_GAME || w->n3ds_native_layout || N3DSIsManagementWindow(w->window_class));
}

void N3DSRequestStationPicker(bool begin)
{
 if (begin) _station_picker_request = 1;
 else if (_station_picker_active || _station_picker_request == 1) _station_picker_request = 2;
}

static void ProcessN3DSStationPicker()
{
 if (_station_picker_request == 0) return;
 if (_station_picker_request == 2 && _pad_held) return;
 const bool begin = _station_picker_request == 1 && (_game_mode == GM_NORMAL || _game_mode == GM_EDITOR);
 if (begin && _upper_ui) SetN3DSUpperUi(false, true);
 _station_picker_request = 0;
 _build_buttons.Reset();
 _left_button_down = _left_button_clicked = _pad_held = _touch_held = false;
 HandleMouseEvents();
 _station_picker_active = begin;
 _map_pad = begin;
 if (begin) _map_ui_front = N3DSFrontUi();
 SelectN3DSInput(begin);
 if (!begin) CenterN3DSMapCursor();
 _panel_needs_draw = true;
 MarkWholeScreenDirty();
}

/** Scrollbar gestures never reach an underlying game widget. */
static bool _canvas_touch=false,_canvas_pending=false;
static WindowClass _canvas_class;static WindowNumber _canvas_number;
static int _canvas_target_x,_canvas_target_y,_canvas_drag_axis=0,_canvas_grab=0;
static Window *N3DSCanvasFront()
{
 Window *w=N3DSFrontUi();
 if((_game_mode != GM_NORMAL && _game_mode != GM_EDITOR)||_map_pad||w==NULL||!N3DSUsesScrollableWorkspace(w))return NULL;
 return w;
}
static bool N3DSCanvasOverflow(const Window *w)
{
 return w!=NULL&&(w->width>N3DSMenuScrollBar::ViewWidth(w->height,_upper_ui)||w->height>196);
}
static N3DSMenuScrollBar N3DSCanvasBar(const Window *w,bool vertical)
{
 N3DSMenuScrollBar bar={vertical?22:44,vertical?196:276,
  vertical?196:N3DSMenuScrollBar::ViewWidth(w->height,_upper_ui),
  vertical?w->height:w->width,vertical?w->n3ds_canvas_y:w->n3ds_canvas_x};
 return bar;
}
static bool N3DSCanvasFooterClick(int x,int y)
{
 Window *w=N3DSCanvasFront();
 if(!N3DSCanvasOverflow(w)||x<0||x>=320||y<22||y>=240||_pad_held||_left_button_down)return false;
 bool horizontal=y>=218,vertical=!horizontal&&x>=298&&w->height>196;
 if(!horizontal&&!vertical)return false;
 _canvas_class=w->window_class;_canvas_number=w->window_number;
 _canvas_target_x=w->n3ds_canvas_x;_canvas_target_y=w->n3ds_canvas_y;_canvas_drag_axis=0;
 if(horizontal&&x<44){_canvas_target_x=_canvas_target_y=0;}
 else{
  N3DSMenuScrollBar bar=N3DSCanvasBar(w,vertical);int at=vertical?y:x;
  int target=bar.offset,step=vertical?48:64;
  if(at<bar.TrackStart())target-=step;
  else if(at>=bar.start+bar.length-22)target+=step;
  else if(at>=bar.ThumbStart()&&at<bar.ThumbStart()+bar.ThumbLength()){
   _canvas_drag_axis=vertical?2:1;_canvas_grab=at-bar.ThumbStart();
  }else target+=(at<bar.ThumbStart()?-bar.view:bar.view);
  if(vertical)_canvas_target_y=bar.Clamp(target,0,bar.Maximum());
  else _canvas_target_x=bar.Clamp(target,0,bar.Maximum());
 }
 _canvas_pending=true;_canvas_touch=true;_touch_held=true;return true;
}
static void MoveN3DSCanvasDrag(int x,int y)
{
 if(_canvas_drag_axis==0)return;Window *w=N3DSCanvasFront();
 if(w==NULL||w->window_class!=_canvas_class||w->window_number!=_canvas_number)return;
 bool vertical=_canvas_drag_axis==2;N3DSMenuScrollBar bar=N3DSCanvasBar(w,vertical);
 int target=bar.OffsetForThumb(vertical?y:x,_canvas_grab);
 if(vertical)_canvas_target_y=target;else _canvas_target_x=target;
 _canvas_pending=true;
}
static void ProcessN3DSCanvasMove()
{
 if(!_canvas_pending||_pad_held||_left_button_down||(_touch_held&&_canvas_drag_axis==0))return;
 _canvas_pending=false;Window *w=N3DSCanvasFront();
 if(w==NULL||w->window_class!=_canvas_class||w->window_number!=_canvas_number)return;
 w->n3ds_canvas_x=_canvas_target_x;w->n3ds_canvas_y=_canvas_target_y;
 w->OnN3DSScreenChange(_upper_ui);_panel_needs_draw=true;MarkWholeScreenDirty();
}
static void DrawN3DSCanvasFooter()
{
 Window *w=N3DSCanvasFront();if(!N3DSCanvasOverflow(w))return;
 DrawPixelInfo footer=_screen;
 footer.dst_ptr=(byte *)_sdl_screen->pixels+240*_sdl_screen->pitch+40*_sdl_screen->format->BytesPerPixel;
 footer.width=320;footer.height=240;footer.left=footer.top=0;footer.zoom=ZOOM_LVL_NORMAL;
 DrawPixelInfo *saved=_cur_dpi;_cur_dpi=&footer;
 DrawFrameRect(0,218,43,239,COLOUR_GREY,FR_NONE);DoDrawStringCentered(22,224,"Home",TC_WHITE);
 for(int axis=0;axis<2;axis++){
  bool vertical=axis!=0;if(vertical&&w->height<=196)continue;
  N3DSMenuScrollBar bar=N3DSCanvasBar(w,vertical);int pos=bar.ThumbStart(),size=bar.ThumbLength();
  if(vertical){
   DrawFrameRect(298,22,319,217,COLOUR_GREY,FR_LOWERED);
   DrawFrameRect(298,22,319,43,COLOUR_GREY,FR_NONE);DrawFrameRect(298,196,319,217,COLOUR_GREY,FR_NONE);
   DoDrawStringCentered(309,28,"^",TC_WHITE);DoDrawStringCentered(309,202,"v",TC_WHITE);
   DrawFrameRect(300,pos,317,pos+size-1,COLOUR_GREY,FR_NONE);
  }else{
   DrawFrameRect(44,218,319,239,COLOUR_GREY,FR_LOWERED);
   DrawFrameRect(44,218,65,239,COLOUR_GREY,FR_NONE);DrawFrameRect(298,218,319,239,COLOUR_GREY,FR_NONE);
   DoDrawStringCentered(55,224,"<",TC_WHITE);DoDrawStringCentered(309,224,">",TC_WHITE);
   DrawFrameRect(pos,220,pos+size-1,237,COLOUR_GREY,FR_NONE);
  }
 }
 _cur_dpi=saved;
}

static void DrawN3DSPanel()
{
 CheckN3DSUpperUi();
 if(_depot_focus_active&&N3DSUpperTrainDepot()==NULL)SetN3DSDepotFocus(false);
 if (_upper_ui) {
  const int bytes = _sdl_screen->format->BytesPerPixel;
  for (int y = 0; y < 240; y++) memcpy((byte *)_sdl_screen->pixels + y * _sdl_screen->pitch, (byte *)_ui_surface->pixels + y * _ui_surface->pitch, 400 * bytes);
 }
 if (_map_pad && !_pad_held && N3DSFrontUi() != _map_ui_front) {
  /* Reveal new dialogs, preserving their pending tool workflow. */
  _map_pad = false;
  SelectN3DSInput(false);
  if (_game_mode != GM_MENU) CenterN3DSMapCursor();
 }
 if (_game_mode == GM_MENU && _map_pad) {
  _map_pad = false;
  SelectN3DSInput(false);
 }
	if (!_map_pad && !_upper_ui) {
		/* Fit the complete legacy 400-pixel desktop into the 320-pixel touch screen.
			* A separate source buffer avoids aliasing during horizontal resampling. */
		int bytes = _sdl_screen->format->BytesPerPixel;
		const bool native_title = NativeN3DSTitle();
		for (int y = 0; y < 240; y++) {
			const byte *src = (const byte *)_ui_surface->pixels + y * _ui_surface->pitch;
			byte *dst = (byte *)_sdl_screen->pixels + (y + 240) * _sdl_screen->pitch + 40 * bytes;
			if (native_title || NativeN3DSToolbarRow(y) || NativeN3DSDropdownRow(y) || NativeN3DSOrdersRow(y)) {
    memcpy(dst, src + 40 * bytes, 320 * bytes);
   } else if (bytes == 1) {
    for (int x = 0; x < 320; x++) dst[x] = src[x * 5 / 4];
   } else {
    for (int x = 0; x < 320; x++) memcpy(dst + x * bytes, src + (x * 5 / 4) * bytes, bytes);
   }
		}
		DrawN3DSCanvasFooter();
		return;
	}
	DrawPixelInfo panel = _screen;
	panel.dst_ptr = (byte *)_sdl_screen->pixels + 240 * _sdl_screen->pitch + 40 * _sdl_screen->format->BytesPerPixel;
	panel.width = 320;
	panel.height = 240;
	panel.left = panel.top = 0;
	panel.zoom = ZOOM_LVL_NORMAL;
	DrawPixelInfo *saved = _cur_dpi;
	_cur_dpi = &panel;
	DrawFrameRect(0, 0, 319, 239, COLOUR_GREY, FR_NONE);
	DoDrawStringCentered(160, 12, N3DSDepotFocus()?"DEPOT CONTROL":_upper_ui ? "MENU CONTROL" : (_station_picker_active ? "SELECT STATION" : "MAP CONTROL"), TC_WHITE);
	DrawFrameRect(6, 34, 313, 193, COLOUR_GREY, FR_LOWERED);
	DoDrawStringCentered(160, 85, (_upper_ui||N3DSDepotFocus()) ? "Touchpad: move the pointer" : "Drag gently to move the cursor", TC_WHITE);
	DoDrawStringCentered(160, 105, (_upper_ui||N3DSDepotFocus()) ? "L / A: click or hold" : (_station_picker_active ? "L / A: choose station   B: cancel" : "L: click / hold L and drag to build"), TC_WHITE);
	const Window *front = N3DSFrontUi();
	if (_upper_ui && front != NULL && N3DSIsMapConstructionWindow(front->window_class)) DoDrawStringCentered(160, 175, "X: use selected tool on map", TC_WHITE);
	DoDrawStringCentered(160, 207, N3DSDepotFocus()?"X / Y / SELECT: return to shopping":_upper_ui ? "Y / SELECT: return menu to bottom" : "SELECT / X: return to tools", TC_WHITE);
	DoDrawStringCentered(160, 223, (_upper_ui||N3DSDepotFocus()) ? "Circle Pad: pointer  D-pad: scroll" : "Circle Pad: scroll   R/Y: zoom   B: cancel", TC_WHITE);
	_cur_dpi = saved;
 DrawN3DSCanvasFooter();
}

static void MoveN3DSTouch(int x, int y)
{
 if(_canvas_touch){MoveN3DSCanvasDrag(x,y);return;}
 if (_upper_ui||N3DSDepotFocus()) {
  if (_touch_held) {
   const Point old = _cursor.pos;
   _cursor.pos.x = Clamp(old.x + x - _last_touch_x, 0, 399);
   _cursor.pos.y = Clamp(old.y + y - _last_touch_y, 0, 239);
   _cursor.delta.x = _cursor.pos.x - old.x;
   _cursor.delta.y = _cursor.pos.y - old.y;
   if(N3DSDepotFocus())_n3ds_map_cursor=_cursor.pos;else _ui_cursor = _cursor.pos;
   _cursor.dirty = true;
   HandleMouseEvents();
  }
  _last_touch_x = x; _last_touch_y = y;
  return;
 }
	if (_n3ds_map_input) {
		if (_touch_held) {
			/* Relative one-to-one movement: lifting the stylus never jumps the cursor. */
			int nx = max(0, min(399, _cursor.pos.x + x - _last_touch_x));
			int ny = max(0, min(227, _cursor.pos.y + y - _last_touch_y));
			_cursor.delta.x = nx - _cursor.pos.x;
			_cursor.delta.y = ny - _cursor.pos.y;
			_cursor.pos.x = nx; _cursor.pos.y = ny;
			_n3ds_map_cursor = _cursor.pos;
		}
	} else {
		int nx = max(0, min(399, (NativeN3DSTitle() || NativeN3DSToolbarRow(y) || NativeN3DSDropdownRow(y) || NativeN3DSOrdersRow(y)) ? x + 40 : x * 400 / 320));
		int ny = max(0, min(239, y));
		_cursor.delta.x = nx - _cursor.pos.x;
		_cursor.delta.y = ny - _cursor.pos.y;
		_cursor.pos.x = nx; _cursor.pos.y = ny;
		_ui_cursor = _cursor.pos;
	}
	_last_touch_x = x; _last_touch_y = y;
	_cursor.in_window = true;
	_cursor.dirty = true;
	HandleMouseEvents();
}
#endif

#define MAX_DIRTY_RECTS 100
static SDL_Rect _dirty_rects[MAX_DIRTY_RECTS];
static int _num_dirty_rects;

void VideoDriver_SDL::MakeDirty(int left, int top, int width, int height)
{
	if (_num_dirty_rects < MAX_DIRTY_RECTS) {
		_dirty_rects[_num_dirty_rects].x = left;
		_dirty_rects[_num_dirty_rects].y = top;
		_dirty_rects[_num_dirty_rects].w = width;
		_dirty_rects[_num_dirty_rects].h = height;
	}
	_num_dirty_rects++;
}

static void UpdatePalette(uint start, uint count)
{
	SDL_Color pal[256];

	for (uint i = 0; i != count; i++) {
		pal[i].r = _cur_palette[start + i].r;
		pal[i].g = _cur_palette[start + i].g;
		pal[i].b = _cur_palette[start + i].b;
		pal[i].unused = 0;
	}

	SDL_CALL SDL_SetColors(_sdl_screen, pal, start, count);
}

static void InitPalette()
{
	UpdatePalette(0, 256);
}

static void CheckPaletteAnim()
{
	if (_pal_count_dirty != 0) {
		Blitter *blitter = BlitterFactoryBase::GetCurrentBlitter();

		switch (blitter->UsePaletteAnimation()) {
			case Blitter::PALETTE_ANIMATION_VIDEO_BACKEND:
				UpdatePalette(_pal_first_dirty, _pal_count_dirty);
				break;

			case Blitter::PALETTE_ANIMATION_BLITTER:
				blitter->PaletteAnimate(_pal_first_dirty, _pal_count_dirty);
				break;

			case Blitter::PALETTE_ANIMATION_NONE:
				break;

			default:
				NOT_REACHED();
		}
		_pal_count_dirty = 0;
	}
}

static void DrawSurfaceToScreen()
{
	#ifdef N3DS
	if (_num_dirty_rects == 0 && !_panel_needs_draw) return;
	DrawN3DSPanel();
	_panel_needs_draw = false;
	_num_dirty_rects = 0;
	SDL_UpdateRect(_sdl_screen, 0, 0, 0, 0);
	return;
#endif
	int n = _num_dirty_rects;
	if (n == 0) return;

	_num_dirty_rects = 0;
	if (n > MAX_DIRTY_RECTS) {
		SDL_CALL SDL_UpdateRect(_sdl_screen, 0, 0, 0, 0);
	} else {
		SDL_CALL SDL_UpdateRects(_sdl_screen, n, _dirty_rects);
	}
}

static const Dimension _default_resolutions[] = {
	{ 640,  480},
	{ 800,  600},
	{1024,  768},
	{1152,  864},
	{1280,  800},
	{1280,  960},
	{1280, 1024},
	{1400, 1050},
	{1600, 1200},
	{1680, 1050},
	{1920, 1200}
};

static void GetVideoModes()
{
	SDL_Rect **modes = SDL_CALL SDL_ListModes(NULL, SDL_SWSURFACE | SDL_FULLSCREEN);
	if (modes == NULL) usererror("sdl: no modes available");

	_all_modes = (SDL_CALL SDL_ListModes(NULL, SDL_SWSURFACE | (_fullscreen ? SDL_FULLSCREEN : 0)) == (void*)-1);
	if (modes == (void*)-1) {
		int n = 0;
		for (uint i = 0; i < lengthof(_default_resolutions); i++) {
			if (SDL_CALL SDL_VideoModeOK(_default_resolutions[i].width, _default_resolutions[i].height, 8, SDL_FULLSCREEN) != 0) {
				_resolutions[n] = _default_resolutions[i];
				if (++n == lengthof(_resolutions)) break;
			}
		}
		_num_resolutions = n;
	} else {
		int n = 0;
		for (int i = 0; modes[i]; i++) {
			int w = modes[i]->w;
			int h = modes[i]->h;
			int j;
			for (j = 0; j < n; j++) {
				if (_resolutions[j].width == w && _resolutions[j].height == h) break;
			}

			if (j == n) {
				_resolutions[j].width  = w;
				_resolutions[j].height = h;
				if (++n == lengthof(_resolutions)) break;
			}
		}
		_num_resolutions = n;
		SortResolutions(_num_resolutions);
	}
}

static void GetAvailableVideoMode(int *w, int *h)
{
	/* All modes available? */
	if (_all_modes || _num_resolutions == 0) return;

	/* Is the wanted mode among the available modes? */
	for (int i = 0; i != _num_resolutions; i++) {
		if (*w == _resolutions[i].width && *h == _resolutions[i].height) return;
	}

	/* Use the closest possible resolution */
	int best = 0;
	uint delta = abs((_resolutions[0].width - *w) * (_resolutions[0].height - *h));
	for (int i = 1; i != _num_resolutions; ++i) {
		uint newdelta = abs((_resolutions[i].width - *w) * (_resolutions[i].height - *h));
		if (newdelta < delta) {
			best = i;
			delta = newdelta;
		}
	}
	*w = _resolutions[best].width;
	*h = _resolutions[best].height;
}

#ifndef ICON_DIR
#define ICON_DIR "media"
#endif

#ifdef WIN32
/* Let's redefine the LoadBMP macro with because we are dynamically
	* loading SDL and need to 'SDL_CALL' all functions */
#undef SDL_LoadBMP
#define SDL_LoadBMP(file)	SDL_LoadBMP_RW(SDL_CALL SDL_RWFromFile(file, "rb"), 1)
#endif

static bool CreateMainSurface(int w, int h)
{
	SDL_Surface *newscreen, *icon;
	char caption[50];
	int bpp = BlitterFactoryBase::GetCurrentBlitter()->GetScreenDepth();

	#ifdef N3DS
	w = 400;
	h = 240;
#else
	GetAvailableVideoMode(&w, &h);
#endif

	DEBUG(driver, 1, "SDL: using mode %dx%dx%d", w, h, bpp);

	if (bpp == 0) usererror("Can't use a blitter that blits 0 bpp for normal visuals");

	/* Give the application an icon */
	icon = SDL_CALL SDL_LoadBMP(ICON_DIR PATHSEP "openttd.32.bmp");
	if (icon != NULL) {
		/* Get the colourkey, which will be magenta */
		uint32 rgbmap = SDL_CALL SDL_MapRGB(icon->format, 255, 0, 255);

		SDL_CALL SDL_SetColorKey(icon, SDL_SRCCOLORKEY, rgbmap);
		SDL_CALL SDL_WM_SetIcon(icon, NULL);
		SDL_CALL SDL_FreeSurface(icon);
	}

	#ifdef N3DS
 /* Restore from the old cursor surface before SDL frees either buffer. */
 UndrawMouseCursor();
#endif
 /* DO NOT CHANGE TO HWSURFACE, IT DOES NOT WORK */
	#ifndef N3DS
		newscreen = SDL_CALL SDL_SetVideoMode(w, h, bpp, SDL_SWSURFACE | SDL_HWPALETTE | (_fullscreen ? SDL_FULLSCREEN : SDL_RESIZABLE));
	#else
			// Upper half is gameplay; lower half is the stylus control panel.
	 	newscreen = SDL_CALL SDL_SetVideoMode(w, h * 2, bpp, SDL_SWSURFACE | 0x00300000 /* SDL_DUALSCR */);
		#endif
	if (newscreen == NULL) {
		DEBUG(driver, 0, "SDL: Couldn't allocate a window to draw on");
		return false;
	}

	_screen.width = newscreen->w;
	#ifdef N3DS
	_screen.height = 240;
	_panel_needs_draw = true;
	_cur_resolution.width = 400;
	_cur_resolution.height = 240;
#else
	_screen.height = newscreen->h;
#endif
	_screen.pitch = newscreen->pitch / (bpp / 8);
	_sdl_screen = newscreen;
#ifdef N3DS
	if (_ui_surface != NULL) SDL_FreeSurface(_ui_surface);
	_ui_surface = SDL_CreateRGBSurface(SDL_SWSURFACE, newscreen->pitch / (bpp / 8), 240, bpp, 0, 0, 0, 0);
	if (_ui_surface == NULL || _ui_surface->pitch != newscreen->pitch) return false;
	_n3ds_ui_pixels = _ui_surface->pixels;
	N3DSBootLog(false, "UI layer: 400x240, pitch %d", _ui_surface->pitch);
#endif
	InitPalette();

	snprintf(caption, sizeof(caption), "OpenTTD %s", _openttd_revision);
	SDL_CALL SDL_WM_SetCaption(caption, caption);
	SDL_CALL SDL_ShowCursor(0);

	GameSizeChanged();

	return true;
}

struct VkMapping {
	uint16 vk_from;
	byte vk_count;
	byte map_to;
};

#define AS(x, z) {x, 0, z}
#define AM(x, y, z, w) {x, y - x, z}

static const VkMapping _vk_mapping[] = {
	/* Pageup stuff + up/down */
	AM(SDLK_PAGEUP, SDLK_PAGEDOWN, WKC_PAGEUP, WKC_PAGEDOWN),
	AS(SDLK_UP,     WKC_UP),
	AS(SDLK_DOWN,   WKC_DOWN),
	AS(SDLK_LEFT,   WKC_LEFT),
	AS(SDLK_RIGHT,  WKC_RIGHT),

	AS(SDLK_HOME,   WKC_HOME),
	AS(SDLK_END,    WKC_END),

	AS(SDLK_INSERT, WKC_INSERT),
	AS(SDLK_DELETE, WKC_DELETE),

	/* Map letters & digits */
	AM(SDLK_a, SDLK_z, 'A', 'Z'),
	AM(SDLK_0, SDLK_9, '0', '9'),

	AS(SDLK_ESCAPE,    WKC_ESC),
	AS(SDLK_PAUSE,     WKC_PAUSE),
	AS(SDLK_BACKSPACE, WKC_BACKSPACE),

	AS(SDLK_SPACE,     WKC_SPACE),
	AS(SDLK_RETURN,    WKC_RETURN),
	AS(SDLK_TAB,       WKC_TAB),

	/* Function keys */
	AM(SDLK_F1, SDLK_F12, WKC_F1, WKC_F12),

	/* Numeric part. */
	AM(SDLK_KP0, SDLK_KP9, '0', '9'),
	AS(SDLK_KP_DIVIDE,   WKC_NUM_DIV),
	AS(SDLK_KP_MULTIPLY, WKC_NUM_MUL),
	AS(SDLK_KP_MINUS,    WKC_NUM_MINUS),
	AS(SDLK_KP_PLUS,     WKC_NUM_PLUS),
	AS(SDLK_KP_ENTER,    WKC_NUM_ENTER),
	AS(SDLK_KP_PERIOD,   WKC_NUM_DECIMAL),

	/* Other non-letter keys */
	AS(SDLK_SLASH,        WKC_SLASH),
	AS(SDLK_SEMICOLON,    WKC_SEMICOLON),
	AS(SDLK_EQUALS,       WKC_EQUALS),
	AS(SDLK_LEFTBRACKET,  WKC_L_BRACKET),
	AS(SDLK_BACKSLASH,    WKC_BACKSLASH),
	AS(SDLK_RIGHTBRACKET, WKC_R_BRACKET),

	AS(SDLK_QUOTE,   WKC_SINGLEQUOTE),
	AS(SDLK_COMMA,   WKC_COMMA),
	AS(SDLK_MINUS,   WKC_MINUS),
	AS(SDLK_PERIOD,  WKC_PERIOD)
};

static uint32 ConvertSdlKeyIntoMy(SDL_keysym *sym)
{
	const VkMapping *map;
	uint key = 0;

	for (map = _vk_mapping; map != endof(_vk_mapping); ++map) {
		if ((uint)(sym->sym - map->vk_from) <= map->vk_count) {
			key = sym->sym - map->vk_from + map->map_to;
			break;
		}
	}

	/* check scancode for BACKQUOTE key, because we want the key left of "1", not anything else (on non-US keyboards) */
#if defined(WIN32) || defined(__OS2__)
	if (sym->scancode == 41) key = WKC_BACKQUOTE;
#elif defined(__APPLE__)
	if (sym->scancode == 10) key = WKC_BACKQUOTE;
#elif defined(__MORPHOS__)
	if (sym->scancode == 0)  key = WKC_BACKQUOTE;  // yes, that key is code '0' under MorphOS :)
#elif defined(__BEOS__)
	if (sym->scancode == 17) key = WKC_BACKQUOTE;
#elif defined(__SVR4) && defined(__sun)
	if (sym->scancode == 60) key = WKC_BACKQUOTE;
	if (sym->scancode == 49) key = WKC_BACKSPACE;
#elif defined(__sgi__)
	if (sym->scancode == 22) key = WKC_BACKQUOTE;
#else
	if (sym->scancode == 49) key = WKC_BACKQUOTE;
#endif

	/* META are the command keys on mac */
	if (sym->mod & KMOD_META)  key |= WKC_META;
	if (sym->mod & KMOD_SHIFT) key |= WKC_SHIFT;
	if (sym->mod & KMOD_CTRL)  key |= WKC_CTRL;
	if (sym->mod & KMOD_ALT)   key |= WKC_ALT;

	return (key << 16) + sym->unicode;
}

static int PollEvent()
{
	SDL_Event ev;

	if (!SDL_CALL SDL_PollEvent(&ev)) return -2;

	switch (ev.type) {
		case SDL_MOUSEMOTION:
#ifdef N3DS
			_panel_x = ev.motion.x - 40;
			_panel_y = ev.motion.y - 240;
			MoveN3DSTouch(_panel_x, _panel_y);
			break;
#endif
			if (_cursor.fix_at) {
				int dx = ev.motion.x - _cursor.pos.x;
				int dy = ev.motion.y - _cursor.pos.y;
				if (dx != 0 || dy != 0) {
					_cursor.delta.x += dx;
					_cursor.delta.y += dy;
					SDL_CALL SDL_WarpMouse(_cursor.pos.x, _cursor.pos.y);
				}
			} else {
				_cursor.delta.x = ev.motion.x - _cursor.pos.x;
				_cursor.delta.y = ev.motion.y - _cursor.pos.y;
				_cursor.pos.x = ev.motion.x;
				_cursor.pos.y = ev.motion.y;
				_cursor.dirty = true;
			}
			HandleMouseEvents();
			break;

		case SDL_MOUSEBUTTONDOWN:
#ifdef N3DS
			if (ev.button.button == SDL_BUTTON_LEFT) {
    if(N3DSCanvasFooterClick(_panel_x,_panel_y))break;
    if (!_n3ds_map_input) MoveN3DSTouch(_panel_x, _panel_y);
    _touch_held = true;
				_last_touch_x = _panel_x; _last_touch_y = _panel_y;
				if (!_n3ds_map_input && !_upper_ui) {
					_left_button_down = true;
					HandleMouseEvents();
				}
			}
			break;
#endif
			if (_rightclick_emulate && SDL_CALL SDL_GetModState() & KMOD_CTRL) {
				ev.button.button = SDL_BUTTON_RIGHT;
			}

			switch (ev.button.button) {
				case SDL_BUTTON_LEFT:
					_left_button_down = true;
					break;

				case SDL_BUTTON_RIGHT:
					_right_button_down = true;
					_right_button_clicked = true;
					break;

				case SDL_BUTTON_WHEELUP:   _cursor.wheel--; break;
				case SDL_BUTTON_WHEELDOWN: _cursor.wheel++; break;

				default: break;
			}
			HandleMouseEvents();
			break;

		case SDL_MOUSEBUTTONUP:
#ifdef N3DS
			if (ev.button.button == SDL_BUTTON_LEFT) {
    if(_canvas_touch){_canvas_touch=false;_touch_held=false;_canvas_drag_axis=0;break;}
				_touch_held = false;
				_left_button_down = _pad_held;
    /* L/A may remain held while the stylus lifts and reanchors. */
    if (!_pad_held) _left_button_clicked = false;
				HandleMouseEvents();
			}
			break;
#endif
			if (_rightclick_emulate) {
				_right_button_down = false;
				_left_button_down = false;
				_left_button_clicked = false;
			} else if (ev.button.button == SDL_BUTTON_LEFT) {
				_left_button_down = false;
				_left_button_clicked = false;
			} else if (ev.button.button == SDL_BUTTON_RIGHT) {
				_right_button_down = false;
			}
			HandleMouseEvents();
			break;

		
#ifdef N3DS
		case SDL_JOYBUTTONDOWN:
		case SDL_JOYBUTTONUP: {
			bool down = ev.type == SDL_JOYBUTTONDOWN;
   if(N3DSUpperTrainDepot()!=NULL&&down&&(ev.jbutton.button==3||ev.jbutton.button==4||ev.jbutton.button==7)){SetN3DSDepotFocus(!N3DSDepotFocus());break;}

   if (down && ev.jbutton.button == 4 && (_upper_ui || !_map_pad)) {
    SetN3DSUpperUi(!_upper_ui);
    break;
   }
   if (_upper_ui||N3DSDepotFocus()) {
    if (ev.jbutton.button == 1 || ev.jbutton.button == 5) {
     _build_buttons.Set(ev.jbutton.button, down);
     _left_button_down = _pad_held = _build_buttons.Held();
     if (!_pad_held) _left_button_clicked = false;
     HandleMouseEvents();
    } else if (down) {
     switch (ev.jbutton.button) {
      case 7: SetN3DSUpperUi(false); break;
      case 2: HandleKeypress(uint32(WKC_ESC) << 16); break;
      case 3: {
       Window *front=N3DSFrontUi();
       if(front!=NULL && N3DSIsMapConstructionWindow(front->window_class)) {
        SetN3DSUpperUi(false,true);_map_pad=true;_map_ui_front=N3DSFrontUi();SelectN3DSInput(true);
        _panel_needs_draw=true;MarkWholeScreenDirty();
       } else { _cursor.wheel--;HandleMouseEvents(); }
       break;
      }
      case 6: _cursor.wheel++; HandleMouseEvents(); break;
      case 0: HandleKeypress(uint32(WKC_PAUSE) << 16); break;
     }
    }
    break;
   }
			if (N3DSBuildButtons::Recognises(ev.jbutton.button, _map_pad)) {
    if (_game_mode == GM_MENU && down) break;
    const bool was_held = _build_buttons.Held();
    _build_buttons.Set(ev.jbutton.button, down);
    _pad_held = _build_buttons.Held();
    if (!was_held && _pad_held) {
     /* A in normal mode inspects, even if a tool was selected in the UI. */
     if (!_map_pad) ResetObjectToPlace();
     /* End any UI touch gesture before beginning a map gesture. */
     _left_button_down = false;
     _left_button_clicked = false;
     HandleMouseEvents();
     SelectN3DSInput(true);
    }
    _left_button_down = _pad_held;
    if (!_pad_held) _left_button_clicked = false;
    HandleMouseEvents();
    if (!_pad_held) SelectN3DSInput(_map_pad);
   } else if (down) {
				switch (ev.jbutton.button) {
					case 2: HandleKeypress(uint32(WKC_ESC) << 16); break;
					case 7: // SELECT lets the left thumb switch modes without dropping the stylus.
     case 3: {
     if (_game_mode == GM_MENU) break;
      /* Abort placement before releasing a drag: exiting must not build it. */
      if (_map_pad) ResetObjectToPlace();
      const bool leaving_construction = _map_pad;
      DeleteWindowByClass(WC_DROPDOWN_MENU);
      _build_buttons.Reset();
      _left_button_down = _left_button_clicked = _pad_held = _touch_held = false;
						HandleMouseEvents();
						_map_pad = !_map_pad;
      if (_map_pad) _map_ui_front = N3DSFrontUi();
						SelectN3DSInput(_map_pad);
      /* Do this after restoring UI input, which saves the old map position. */
      if (leaving_construction) CenterN3DSMapCursor();
      _panel_needs_draw = true;
						MarkWholeScreenDirty();
						break;
     }
					case 5: HandleKeypress(uint32(WKC_MINUS) << 16); break; // Normal mode: L zooms out.
     case 4: if (_map_pad) HandleKeypress(uint32(WKC_MINUS) << 16); break; // Construction: Y zooms out.
					case 6: HandleKeypress(uint32(WKC_EQUALS) << 16); break;
					case 0: if (_game_mode != GM_MENU) HandleKeypress(uint32(WKC_PAUSE) << 16); break;
				}
			}
			break;
		}
#endif
		case SDL_ACTIVEEVENT:
			if (!(ev.active.state & SDL_APPMOUSEFOCUS)) break;

			if (ev.active.gain) { // mouse entered the window, enable cursor
				_cursor.in_window = true;
			} else {
				UndrawMouseCursor(); // mouse left the window, undraw cursor
				_cursor.in_window = false;
			}
			break;

		case SDL_QUIT:
			HandleExitGameRequest();
			break;

		case SDL_KEYDOWN: // Toggle full-screen on ALT + ENTER/F
			if ((ev.key.keysym.mod & (KMOD_ALT | KMOD_META)) &&
					(ev.key.keysym.sym == SDLK_RETURN || ev.key.keysym.sym == SDLK_f)) {
				ToggleFullScreen(!_fullscreen);
			} else {
				HandleKeypress(ConvertSdlKeyIntoMy(&ev.key.keysym));
			}
			break;

		case SDL_VIDEORESIZE: {
			int w = max(ev.resize.w, 64);
			int h = max(ev.resize.h, 64);
			ChangeResInGame(w, h);
			break;
		}
	}
	return -1;
}

const char *VideoDriver_SDL::Start(const char * const *parm)
{
	char buf[30];

	#ifndef N3DS
	const char *s = SdlOpen(SDL_INIT_VIDEO);
	#else
	const char *s = SdlOpen(SDL_INIT_VIDEO|SDL_INIT_JOYSTICK);
	#endif /* N3DS */ 
	N3DSBootLog(false, "SDL init: %s", s == NULL ? "ready" : s);
	if (s != NULL) return s;

	SDL_CALL SDL_VideoDriverName(buf, 30);
	DEBUG(driver, 1, "SDL: using driver '%s'", buf);

	GetVideoModes();
	N3DSBootLog(false, "Creating SDL surface %dx%d", _cur_resolution.width, _cur_resolution.height);
	if (!CreateMainSurface(_cur_resolution.width, _cur_resolution.height)) {
		N3DSBootLog(false, "SDL surface failed: %s", SDL_GetError());
		return "Could not create SDL surface";
	}
	N3DSBootLog(false, "SDL surface ready");
	MarkWholeScreenDirty();

	SDL_CALL SDL_EnableKeyRepeat(SDL_DEFAULT_REPEAT_DELAY, SDL_DEFAULT_REPEAT_INTERVAL);
	SDL_CALL SDL_EnableUNICODE(1);
	
	#ifdef N3DS
	N3DSBootLog(false, "Revival r3: map above / window desktop below; X switches map pad");
	
	// Enable the 3DS's controls to be used as a joystick.
	_3ds_joystick = SDL_JoystickOpen(0);
	SDL_JoystickEventState(SDL_ENABLE);
	#endif /* N3DS */
	return NULL;
}

void VideoDriver_SDL::Stop()
{
	SdlClose(SDL_INIT_VIDEO);
}

void VideoDriver_SDL::MainLoop()
{
	N3DSBootLog(false, "Entering game loop");
	uint32 cur_ticks = SDL_CALL SDL_GetTicks();
	uint32 last_cur_ticks = cur_ticks;
	uint32 next_tick = cur_ticks + 30;
	uint32 pal_tick = 0;
	uint32 mod;
	int numkeys;
	Uint8 *keys;

	for (;;) {
		uint32 prev_cur_ticks = cur_ticks; // to check for wrapping
		InteractiveRandom(); // randomness

		while (PollEvent() == -1) {}
		if (_exit_game) return;
		ProcessN3DSMenuScreenChange();
  ProcessN3DSCanvasMove();
		ProcessN3DSStationPicker();

		mod = SDL_CALL SDL_GetModState();
		keys = SDL_CALL SDL_GetKeyState(&numkeys);
#if defined(_DEBUG)
		if (_shift_pressed)
#else
		/* Speedup when pressing tab, except when using ALT+TAB
		 * to switch to another application */
		if (keys[SDLK_TAB] && (mod & KMOD_ALT) == 0)
#endif
		{
			if (!_networking && _game_mode != GM_MENU) _fast_forward |= 2;
		} else if (_fast_forward & 2) {
			_fast_forward = 0;
		}

		cur_ticks = SDL_CALL SDL_GetTicks();
		if (cur_ticks >= next_tick || (_fast_forward && !_pause_game) || cur_ticks < prev_cur_ticks) {
			_realtime_tick += cur_ticks - last_cur_ticks;
			last_cur_ticks = cur_ticks;
			next_tick = cur_ticks + 30;

			bool old_ctrl_pressed = _ctrl_pressed;

			_ctrl_pressed  = !!(mod & KMOD_CTRL);
			_shift_pressed = !!(mod & KMOD_SHIFT);

			/* determine which directional keys are down */
			#ifdef N3DS
			/* Current 3ds-sdl exposes the D-pad as a hat, not joystick buttons. */
			Uint8 dpad = SDL_JoystickGetHat(_3ds_joystick, 0);
			/* Ignore the centre region to avoid Circle Pad drift. */
			const int cx = SDL_JoystickGetAxis(_3ds_joystick, 0);
			const int cy = SDL_JoystickGetAxis(_3ds_joystick, 1);
   if (_upper_ui||N3DSDepotFocus()) {
    const int dx = abs(cx) > 8000 ? (cx < 0 ? -1 : 1) * max(1, (abs(cx) - 8000) * 5 / 24760) : 0;
    const int dy = abs(cy) > 8000 ? (cy < 0 ? -1 : 1) * max(1, (abs(cy) - 8000) * 5 / 24760) : 0;
    const Point old = _cursor.pos;
    _cursor.pos.x = Clamp(old.x + dx, 0, 399);
    _cursor.pos.y = Clamp(old.y + dy, 0, 239);
    _cursor.delta.x = _cursor.pos.x - old.x;
    _cursor.delta.y = _cursor.pos.y - old.y;
    if(N3DSDepotFocus())_n3ds_map_cursor=_cursor.pos;else _ui_cursor = _cursor.pos;
    if (dx != 0 || dy != 0) _cursor.dirty = true;
    static uint scroll_tick = 0;
    if (++scroll_tick >= 4) {
     scroll_tick = 0;
     if (dpad & SDL_HAT_UP) _cursor.wheel--;
     if (dpad & SDL_HAT_DOWN) _cursor.wheel++;
    }
    HandleMouseEvents();
    dpad = 0;
   }
   const int magnitude = max(abs(cx), abs(cy));
   _n3ds_scroll_factor = dpad != 0 ? 10 : max(2, min(10, 2 + (magnitude - 8000) * 8 / 24760));
			if (!_upper_ui && !N3DSDepotFocus() && cx < -8000) dpad |= SDL_HAT_LEFT;
			if (!_upper_ui && !N3DSDepotFocus() && cx > 8000) dpad |= SDL_HAT_RIGHT;
			if (!_upper_ui && !N3DSDepotFocus() && cy < -8000) dpad |= SDL_HAT_UP;
			if (!_upper_ui && !N3DSDepotFocus() && cy > 8000) dpad |= SDL_HAT_DOWN;
			_dirkeys =
				((dpad & SDL_HAT_LEFT)  ? 1 : 0) |
				((dpad & SDL_HAT_UP)    ? 2 : 0) |
				((dpad & SDL_HAT_RIGHT) ? 4 : 0) |
				((dpad & SDL_HAT_DOWN)  ? 8 : 0);
			#else
			_dirkeys =
				(keys[SDLK_LEFT]  ? 1 : 0) |
				(keys[SDLK_UP]    ? 2 : 0) |
				(keys[SDLK_RIGHT] ? 4 : 0) |
				(keys[SDLK_DOWN]  ? 8 : 0);
			#endif

			if (old_ctrl_pressed != _ctrl_pressed) HandleCtrlChanged();

			GameLoop();

			_screen.dst_ptr = _sdl_screen->pixels;
			UpdateWindows();
			if (++pal_tick > 4) {
				CheckPaletteAnim();
				pal_tick = 1;
			}
			DrawSurfaceToScreen();
		} else {
			SDL_CALL SDL_Delay(1);
			_screen.dst_ptr = _sdl_screen->pixels;
			NetworkDrawChatMessage();
			DrawMouseCursor();
			DrawSurfaceToScreen();
		}

		#ifdef N3DS

		/*int heap_size = envGetHeapSize();

		printf("heap size: %d\n\n", heap_size);*/

		#endif
	}
}

bool VideoDriver_SDL::ChangeResolution(int w, int h)
{
	return CreateMainSurface(w, h);
}

bool VideoDriver_SDL::ToggleFullscreen(bool fullscreen)
{
	_fullscreen = fullscreen;
	GetVideoModes(); // get the list of available video modes
	if (_num_resolutions == 0 || !this->ChangeResolution(_cur_resolution.width, _cur_resolution.height)) {
		/* switching resolution failed, put back full_screen to original status */
		_fullscreen ^= true;
		return false;
	}
	return true;
}

#endif /* WITH_SDL */
