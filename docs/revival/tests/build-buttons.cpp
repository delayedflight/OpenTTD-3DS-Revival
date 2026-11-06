// Regression checks for independent A/L press and release ordering.
#include "../../../src/n3ds_controls.h"
#include <cassert>
#include <iostream>
int main()
{
 N3DSBuildButtons b;
 assert(!b.Held());
 b.Set(5, true); assert(b.Held()); // L alone starts a build gesture.
 b.Set(1, true); b.Set(5, false); assert(b.Held()); // A keeps it held.
 b.Set(1, false); assert(!b.Held());
 b.Set(1, true); b.Set(5, true); b.Set(1, false); assert(b.Held());
 b.Set(5, false); assert(!b.Held());
 b.Set(5, true); b.Set(5, true); assert(b.Held());
 b.Set(5, false); assert(!b.Held()); // Repeated down does not require repeated up.
 b.Set(1, false); b.Set(5, false); assert(!b.Held());
 b.Set(4, true); b.Set(6, true); assert(!b.Held()); // Zoom buttons cannot click.
 b.Set(1, true); b.Set(5, true); b.Reset(); assert(!b.Held());
 b.Set(1, false); b.Set(5, false); assert(!b.Held()); // Releases after mode reset.
 std::cout << "A/L ordering, overlap, reset and zoom-button isolation passed\n";
}
