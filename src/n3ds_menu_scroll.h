/** Native gameplay workspace scrollbar geometry; no engine state or allocation. */
#ifndef N3DS_MENU_SCROLL_H
#define N3DS_MENU_SCROLL_H
struct N3DSMenuScrollBar {
 int start, length, view, extent, offset;
 static int Clamp(int value,int low,int high){return value<low?low:(value>high?high:value);}
 int Maximum()const{return extent>view?extent-view:0;}
 int TrackStart()const{return start+22;}
 int TrackLength()const{return length-44;}
 int ThumbLength()const{return extent<=view?TrackLength():Clamp(view*TrackLength()/extent,22,TrackLength());}
 int Travel()const{return TrackLength()-ThumbLength();}
 int ThumbStart()const{return TrackStart()+(Maximum()==0?0:Clamp(offset,0,Maximum())*Travel()/Maximum());}
 int OffsetForThumb(int coordinate,int grab)const{return Travel()==0?0:Clamp(coordinate-grab-TrackStart(),0,Travel())*Maximum()/Travel();}
 static int ViewWidth(int height,bool upper){return upper?400:(height>196?298:320);}
};
#endif
