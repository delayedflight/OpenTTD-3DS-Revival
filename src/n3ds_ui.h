/** 3DS split-screen routing. UI coordinates are logical 400x240. */
#ifndef N3DS_UI_H
#define N3DS_UI_H
#ifdef N3DS
#include "core/geometry_type.hpp"
#include "gfx_type.h"
#include "window_type.h"
extern void *_n3ds_ui_pixels;
extern void *_n3ds_cursor_surface;
extern bool _n3ds_map_input;
bool N3DSUpperUiActive();
bool N3DSUsesScreenPin(WindowClass cls);
bool N3DSIsConstructionWindow(WindowClass cls);
bool N3DSIsMapConstructionWindow(WindowClass cls);
void N3DSRequestMenuScreenChange(WindowClass cls, WindowNumber number);
struct N3DSWidgetLayout { int16 left, right, top, bottom; byte type; };
extern int _n3ds_scroll_factor;
extern Point _n3ds_map_cursor;
/** Defer station-picker mode changes until after the current input callback. */
void N3DSRequestStationPicker(bool begin);
/** Scope the cursor position and drawing surface to the active game mode. */
struct N3DSMapCursorScope {
 Point saved;
 void *saved_surface;
 N3DSMapCursorScope();
 ~N3DSMapCursorScope();
};
#endif
#endif
