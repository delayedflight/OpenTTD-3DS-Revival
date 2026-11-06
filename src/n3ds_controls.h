/** Physical buttons sharing the 3DS map's left mouse button. */
#ifndef N3DS_CONTROLS_H
#define N3DS_CONTROLS_H
class N3DSBuildButtons {
 unsigned int mask;
public:
 N3DSBuildButtons() : mask(0) {}
 static bool Recognises(unsigned int button, bool construction = true) { return button == 1 || (button == 5 && construction); } // A always; L only in map-pad mode
 void Set(unsigned int button, bool down) {
  if (!Recognises(button)) return;
  if (down) mask |= 1u << button;
  else mask &= ~(1u << button);
 }
 bool Held() const { return mask != 0; }
 void Reset() { mask = 0; }
};
#endif
