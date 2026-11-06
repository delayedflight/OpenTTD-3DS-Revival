/** 3DS split-screen routing. UI coordinates are logical 400x240. */
#ifndef N3DS_UI_H
#define N3DS_UI_H
#ifdef N3DS
#include "core/geometry_type.hpp"
extern void *_n3ds_ui_pixels;
extern bool _n3ds_map_input;
extern int _n3ds_scroll_factor;
extern Point _n3ds_map_cursor;
/** Temporarily use the map cursor only while drawing it above. */
struct N3DSMapCursorScope {
 Point saved;
 N3DSMapCursorScope();
 ~N3DSMapCursorScope();
};
#endif
#endif
