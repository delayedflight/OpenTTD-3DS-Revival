
#include <algorithm>
#include <array>
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <iostream>
using uint8 = unsigned char;
#define N3DS 1
const int WC_MAIN_WINDOW=0, WC_STATUS_BAR=1, WC_UI=2, WC_INVALID=-1;
struct Window { int left,top,width,height,window_class; const Window *z_front; };
#define FOR_ALL_WINDOWS_FROM_BACK_FROM(w,start) for(w=start;w!=nullptr;w=w->z_front) if(w->window_class!=WC_INVALID)
struct Point {int x,y;}; Point _vp_move_offs;
struct {void *dst_ptr; int pitch;} _screen;
void *_n3ds_ui_pixels;
struct {bool visible=false;} _cursor;
void UndrawMouseCursor() {}
struct Video {void MakeDirty(int,int,int,int){}} video;Video *_video_driver=&video;
struct Blitter {void ScrollBuffer(void*,int&,int&,int&,int&,int,int);};
struct BlitterFactoryBase {static Blitter *GetCurrentBlitter(){static Blitter b;return &b;}};
void GfxScroll(int,int,int,int,int,int,void *surface=nullptr);
void RedrawScreenRect(int,int,int,int);
std::array<uint8,400*240> topbuf,uibuf;
bool upper; int ox,oy;
int value(int x,int y) {return ((x+ox)*17 ^ (y+oy)*31)&255;}
int topref(int x,int y) {return upper ? (y>=228?42:value(x,y)) : ((x*3+y*5)&255);}
int uiref(int x,int y) {
 if(!upper && x>=20 && x<260 && y>=12 && y<172 && !(x>=100 && x<180 && y>=40 && y<110)) return value(x,y);
 return ((x*7+y*11+161)&255);
}
void RedrawScreenRect(int l,int t,int r,int b) {
 for(int y=t;y<b;y++)for(int x=l;x<r;x++){topbuf[y*400+x]=topref(x,y);uibuf[y*400+x]=uiref(x,y);}
}
void Blitter::ScrollBuffer(void *video, int &left, int &top, int &width, int &height, int scroll_x, int scroll_y)
{
	const uint8 *src;
	uint8 *dst;

	if (scroll_y > 0) {
		/* Calculate pointers */
		dst = (uint8 *)video + left + (top + height - 1) * _screen.pitch;
		src = dst - scroll_y * _screen.pitch;

		/* Decrease height and increase top */
		top += scroll_y;
		height -= scroll_y;
		assert(height > 0);

		/* Adjust left & width */
		if (scroll_x >= 0) {
			dst += scroll_x;
			left += scroll_x;
			width -= scroll_x;
		} else {
			src -= scroll_x;
			width += scroll_x;
		}

		for (int h = height; h > 0; h--) {
			memcpy(dst, src, width * sizeof(uint8));
			src -= _screen.pitch;
			dst -= _screen.pitch;
		}
	} else {
		/* Calculate pointers */
		dst = (uint8 *)video + left + top * _screen.pitch;
		src = dst - scroll_y * _screen.pitch;

		/* Decrese height. (scroll_y is <=0). */
		height += scroll_y;
		assert(height > 0);

		/* Adjust left & width */
		if (scroll_x >= 0) {
			dst += scroll_x;
			left += scroll_x;
			width -= scroll_x;
		} else {
			src -= scroll_x;
			width += scroll_x;
		}

		/* the y-displacement may be 0 therefore we have to use memmove,
		 * because source and destination may overlap */
		for (int h = height; h > 0; h--) {
			memmove(dst, src, width * sizeof(uint8));
			src += _screen.pitch;
			dst += _screen.pitch;
		}
	}
}
void GfxScroll(int left, int top, int width, int height, int xo, int yo, void *surface)
{
	Blitter *blitter = BlitterFactoryBase::GetCurrentBlitter();

	if (xo == 0 && yo == 0) return;

	if (_cursor.visible) UndrawMouseCursor();

#ifdef ENABLE_NETWORK
	NetworkUndrawChatMessage();
#endif /* ENABLE_NETWORK */

	blitter->ScrollBuffer(_screen.dst_ptr, left, top, width, height, xo, yo);
	/* This part of the screen is now dirty. */
	_video_driver->MakeDirty(left, top, width, height);
}
static void DoSetViewportPosition(const Window *w, int left, int top, int width, int height, const Window *owner)
{
	FOR_ALL_WINDOWS_FROM_BACK_FROM(w, w) {
		if (left + width > w->left &&
				w->left + w->width > left &&
				top + height > w->top &&
				w->top + w->height > top) {

			if (left < w->left) {
				DoSetViewportPosition(w, left, top, w->left - left, height, owner);
				DoSetViewportPosition(w, left + (w->left - left), top, width - (w->left - left), height, owner);
				return;
			}

			if (left + width > w->left + w->width) {
				DoSetViewportPosition(w, left, top, (w->left + w->width - left), height, owner);
				DoSetViewportPosition(w, left + (w->left + w->width - left), top, width - (w->left + w->width - left) , height, owner);
				return;
			}

			if (top < w->top) {
				DoSetViewportPosition(w, left, top, width, (w->top - top), owner);
				DoSetViewportPosition(w, left, top + (w->top - top), width, height - (w->top - top), owner);
				return;
			}

			if (top + height > w->top + w->height) {
				DoSetViewportPosition(w, left, top, width, (w->top + w->height - top), owner);
				DoSetViewportPosition(w, left, top + (w->top + w->height - top), width , height - (w->top + w->height - top), owner);
				return;
			}

			return;
		}
	}

	{
		int xo = _vp_move_offs.x;
		int yo = _vp_move_offs.y;

		if (abs(xo) >= width || abs(yo) >= height) {
			/* fully_outside */
			RedrawScreenRect(left, top, left + width, top + height);
			return;
		}

		GfxScroll(left, top, width, height, xo, yo);

		if (xo > 0) {
			RedrawScreenRect(left, top, xo + left, top + height);
			left += xo;
			width -= xo;
		} else if (xo < 0) {
			RedrawScreenRect(left + width + xo, top, left + width, top + height);
			width += xo;
		}

		if (yo > 0) {
			RedrawScreenRect(left, top, width + left, top + yo);
		} else if (yo < 0) {
			RedrawScreenRect(left, top + height + yo, width + left, top + height);
		}
	}
}

int main(){
 int mismatches=0,cases=0;
 const int delta[][2]={{17,0},{-19,0},{0,9},{0,-11},{13,7},{-11,-8},{13,-9},{-17,11},{500,0},{0,300}};
 for(bool mode:{true,false})for(auto &d:delta){
  upper=mode;ox=oy=0;_screen={topbuf.data(),400};_n3ds_ui_pixels=uibuf.data();RedrawScreenRect(0,0,400,240);
  Window status{0,228,400,12,WC_STATUS_BAR,nullptr};
  Window obstacle{upper?120:100,upper?15:40,upper?280:80,upper?210:70,WC_UI,&status};
  Window toolbar{0,0,400,96,WC_UI,&obstacle};
  Window owner{upper?0:20,upper?0:12,upper?400:240,upper?240:160,upper?WC_MAIN_WINDOW:WC_UI,upper?&toolbar:&obstacle};
  _vp_move_offs={d[0],d[1]};ox=-d[0];oy=-d[1];
  DoSetViewportPosition(owner.z_front,owner.left,owner.top,owner.width,owner.height,&owner);
  int errors=0;for(int y=0;y<240;y++)for(int x=0;x<400;x++){errors+=topbuf[y*400+x]!=topref(x,y);errors+=uibuf[y*400+x]!=uiref(x,y);}
  if(errors){std::cout<<(upper?"upper":"lower")<<" dx="<<d[0]<<" dy="<<d[1]<<" mismatched="<<errors<<"\n";mismatches++;}cases++;
 }
 std::cout<<"cases="<<cases<<" failed="<<mismatches<<"\n";return mismatches?1:0;
}
