/** 3DS split-screen routing. UI coordinates are logical 400x240. */
#ifndef N3DS_UI_H
#define N3DS_UI_H
#ifdef N3DS
#include "core/geometry_type.hpp"
#include "gfx_type.h"
extern void *_n3ds_ui_pixels;
extern void *_n3ds_cursor_surface;
extern bool _n3ds_map_input;
extern int _n3ds_scroll_factor;
extern Point _n3ds_map_cursor;
/** Scope the cursor position and drawing surface to the active game mode. */
struct N3DSMapCursorScope {
 Point saved;
 void *saved_surface;
 N3DSMapCursorScope();
 ~N3DSMapCursorScope();
};
#endif
#endif
