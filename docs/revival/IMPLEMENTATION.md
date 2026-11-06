# OpenTTD 3DS Revival implementation guide

This guide describes the r3d inspection-centre refinement of the r3a repair, based on EnergeticBark/OpenTTD-3DS v1.0.1, OpenTTD 0.7.0. The tested r1b repair and r2 UI prototype are preserved separately. r3 needs independent physical-console validation.

## Build and project layout

The complete source distribution contains `source/` and `environment/`. Start Docker Desktop and run `environment/build.command`. The pinned devkitPro image and package setup are specified in `environment/Dockerfile`; `environment/build.sh` contains the exact configure flags. Source is copied into `/build` inside a disposable container because the legacy configure system does not handle paths containing spaces reliably. Build outputs go into `builds/repair-r3d/`: the `.3dsx`, matching `.elf`, languages, and toolchain inventory. Keep the ELF paired with each distributed binary; addresses from one build must not be resolved using another build's symbols.

The upstream checkout, the r1b source, and r2 source are kept separately in the development project. Private saves and crash dumps are local evidence, not release assets. Never test against the user's only save or write a release directly onto their SD card.

## Rendering model

`src/video/sdl_v.cpp` creates a 400 by 480 SDL surface with the 3DS SDL dual-screen flag. OpenTTD continues to see a 400 by 240 logical screen. The first half is the upper map display; the lower half is the physical touchscreen. The SDL backend crops the centre 320 pixels of the lower 400-pixel half, so the displayed pixels start at x=40 and y=240 in the SDL surface.

r3 adds a separate UI surface. Its pitch matches the main SDL surface. `src/window.cpp` selects the destination when painting each window: `WC_MAIN_WINDOW` and `WC_STATUS_BAR` draw into the upper display, and every other window draws into the UI surface. The date/status/money bar occupies the bottom 12 pixels above, leaving all 240 touchscreen rows for UI. Map cursor motion is clamped above that information bar. Occlusion testing ignores windows on the other layer. Without that filter, an invisible menu would still cut a hole in the map beneath it.

The root `_screen.dst_ptr` is scoped to the same target during each window’s `OnPaint`, then restored. This is necessary for specialised painters such as the minimap, whose absolute-buffer bounds checks also use the root surface; changing only the clipped drawing pointer leaves those checks pointed at the wrong allocation.

The UI surface is cleared only in damaged regions before those regions are repainted. This matters when a window closes: its old pixels must disappear. The existing dirty-block mechanism is retained; there is no second OpenTTD simulation and no duplicated window tree. Normal clipping, z-order and original widget callbacks are retained within the UI layer.

The complete 400-pixel desktop is resampled horizontally to 320 physical touchscreen pixels. Vertical coordinates remain 1:1. This is a compatibility bridge for the old window system, not a claim that every desktop dialog has been redesigned. Large dialogs can still need individual adaptations. Native-width title rendering is a special case: the 320-pixel menu is centred in the logical desktop and copied without horizontal resampling while it is frontmost.

`src/n3ds_ui.h` declares the small interface shared by the video, window and cursor code. These changes are guarded by `N3DS`; desktop rendering follows its existing path.

### Scroll optimisation and screen ownership

`DoSetViewportPosition` has a separate occlusion walk from normal window painting. It must filter by physical screen too. In r3 this walk still treated the lower toolbar and AI Debug window as upper-map obstacles; panning skipped moving those rectangles, leaving stale map pixels and repeated fragments. r3a passes the viewport owner through recursive clipping, ignores obstacles on the other display, and preserves the upper status bar as a real upper obstacle.

`GfxScroll` accepts an optional surface pointer. Upper map viewports scroll the upper backing surface; secondary viewports inside lower UI windows scroll the UI backing surface. Omitting this distinction writes cached lower-viewport pixels into the upper map. The existing fast pixel-scroll optimisation is retained rather than forcing an expensive full-map repaint each frame.

## Touch coordinates and input routing

SDL dual-screen touch events include the crop offset and lower-screen offset. Subtract x=40 and y=240 first. Normal UI input then maps physical x to `x*400/320`, with unchanged y. On the native title menu, physical x instead maps to x+40. Rendering and hit testing must use the same transform.

`FindWindowFromPt` filters by input layer: normal touch input can select UI windows but cannot click through to the upper map. Map input can select only the main window. This is separate from drawing: visual z-order alone is insufficient to prevent clicks on the wrong display.

SELECT or X toggles between the UI desktop and a relative map-control pad, allowing a left-thumb mode switch while the right hand keeps the stylus. If a map action opens a new UI window (an error, bridge choice, station join or vehicle detail), the pad returns to the UI after the final L/A build button is released so the new dialog is visible. Tooltip windows are ignored for this transition. On the pad, dragging moves the upper cursor one logical pixel per touch pixel. The first touch records an anchor; lifting and touching again does not jump the cursor. Touching the pad does not itself place anything. L presses the map's left button; holding L while dragging supports normal construction drags. A remains an alternative. `src/n3ds_controls.h` tracks both buttons as a bitmask: releasing either one leaves the drag held if the other remains pressed. Releasing the last one restores the selected input mode. Lifting the stylus while a build button remains held does not reset the mouse-click latch, so the stylus can be repositioned without ending or restarting the drag. Switching modes releases button state before changing layers to prevent a stuck drag.

The map and UI retain separate cursor positions. During gameplay, `N3DSMapCursorScope` temporarily uses the map position and upper surface for drawing. In `GM_MENU`, it instead keeps the input position and draws on the UI surface, so the pointer follows the title menu and its dialogs below. The scope restores the input position, screen destination on exit, then leaves the drawing context at the persistent root `_screen` rather than a window painter’s temporary stack context.

The cursor backup buffer records its owning surface in `_n3ds_cursor_surface`. Undrawing must restore the pixels to that surface, not whichever destination is currently selected. A mode change forces a cursor redraw even if it has not moved. Before a video-mode change, the previous cursor is undrawn before SDL frees either backing surface. This prevents title/game transitions and resolution changes from restoring stale cursor pixels to the wrong screen.

B sends Escape (cancel placement) and START toggles pause. In normal tools/windows mode L/R zoom out/in. In map-pad mode L builds, R zooms in and Y zooms out using the existing shortcuts. These reuse OpenTTD's handlers rather than introducing parallel construction commands. SDL's 3DS joystick button numbers are used here, not raw HID key bit positions.

## Scrolling

D-pad input uses SDL joystick hat 0. Circle Pad input uses axes 0 and 1, with an 8000-unit dead zone on the approximately +/-32760 scale. Beyond that dead zone it contributes directional flags. The scroll factor increases from 2 toward 10 as pad displacement grows; D-pad input keeps factor 10. The existing isometric direction table and `ScrollMainViewport` are retained. Edit-box focus still suppresses key scrolling as in the original engine.

## Touch toolbar layout

`LayoutN3DSToolbars` repositions widgets without changing widget IDs or callbacks. The normal main toolbar displays its 27 real tools in a 9-column, three-row grid: about 35 physical pixels wide by 32 high per target. Its obsolete desktop toolbar-page switch is hidden because all tools are visible. Construction-toolbar image buttons use eight columns, approximately 40 physical pixels wide by 32 high. Caption and sticky controls retain their roles; narrow desktop spacers are removed.

Construction child dialogs are positioned beneath the actual toolbar height where possible and clamped vertically. Large dialogs may overlap the toolbar: its desktop always-on-top rule is disabled on 3DS so essential save and load controls remain reachable. The status bar is excluded from touch hit testing because it is physically above. These rules apply to toolbar classes, not arbitrary dialogs; station-size grids, financial tables, text fields and other specialised windows keep their original behaviour. Each should be tested and adapted deliberately rather than blindly scaling widget coordinates everywhere.

## Title screen and assets

The 3DS title path deliberately uses an empty 64 by 64 backdrop, with no loaded transport network or AI. It does not load the bundled compressed `opntitle.dat`. This avoids the previous compressed-title load failure and provides a predictable small baseline. It is still an engine map, not a separate bitmap-only application; water-palette animation and normal menu engine work can remain.

The OpenTTD title lettering comes from the bundled sprite set. The revival subtitle, menus and control-pad instructions use the game's existing pixel font. No external icon pack or proprietary Transport Tycoon artwork was imported. Existing sprite IDs, frame drawing, palettes and translated menu strings are reused. Some newly added instructional labels remain English.

A custom scenario-editor title scene can be considered later. Start at 64 by 64, with no AI and very few vehicles. Do not silently replace the lightweight baseline with an arbitrary large save. A future title-scene loader should validate size, handle unsupported compression cleanly and fall back safely.

## Memory considerations

For the default 8-bit blitter, r2's dual-screen texture and indexed framebuffer added about 639,488 bytes compared with the original 320 by 240 mode, calculated from the pinned SDL backend's power-of-two texture allocation. r3 adds roughly another 96,000 bytes for the 400 by 240 indexed UI surface, plus SDL surface metadata. These figures are allocation calculations, not measured total process memory or a guarantee of original-3DS headroom. Other blitter depths allocate more. The UI does not load a second graphics pack, duplicate vehicle simulation or clean old save cargo records.

## Stability fixes retained from r1b

`CargoPacket` invalidation must leave its count at zero, and `Company` invalidation must clear its validity marker. The original release's optimised destructors failed to retain those stores. The repair explicitly preserves them, alongside `-fno-lifetime-dse`. This prevents the demonstrated new stale-cargo accumulation and removed-company/null-AI event path. It does not reclaim stale cargo already present in a user's save.

Modern compiler detection and unsupported external MIDI-driver exclusions remain. Startup directory selection and flushed diagnostics are in `src/n3ds_bootlog.h`; the fallback path names are release-specific. Always update the executable directory, fallback argv and log path together for a new release.

Existing SDK/compiler mixed-enum ABI warnings remain and must be disclosed. Emulator success alone does not establish hardware safety or remove that uncertainty.

## Validation workflow

1. Build in the pinned container and retain logs, exact ELF and executable hash.
2. Boot without autoexec scripts. Confirm the title is above and the actual menu below, with no gameplay panel at startup. Verify menu text is native width and direct touches select the matching button.
3. Load a disposable save through the lower-screen load dialog. Confirm no UI window occludes the upper map.
4. Open rail/road/other construction tools below; check enlarged buttons, dropdowns and child pickers. Open and close dialogs to check damaged-region repainting.
5. Switch to the relative pad with X. Repeatedly lift and reposition without pressing L: no building should occur and the cursor should not jump. Press L to place, and hold L while dragging for construction. Return to the UI and check button state is released.
6. Test Circle Pad and D-pad scrolling, dead zone, diagonals, L/R zoom, B cancellation and START pause. Keyboard-emulated analogue input cannot establish physical dead-zone feel; test the real pad too.
7. Save a disposable game through the UI, reload it, and run through monthly autosaves. Confirm the title/menu state after returning from gameplay.
8. Validate ZIP checksums, ensure the source archive includes all new headers and docs, and verify that no private saves or crash dumps are distributed.
9. Repeat on original 3DS XL hardware. Keep the known-working build installed separately and record the action, game date and diagnostic log for failures.

## Known gaps

Not every large legacy dialog has been redesigned. The horizontal compatibility transform can narrow text in in-game dialogs, and some original window minimum sizes exceed the available desktop. No new software keyboard is provided. This is a feature prototype, and physical stylus feel, hardware memory pressure, and longer endurance need separate checks. Network and music work remain outside this release.

## Reproducing the scrolling regression

From the extracted source distribution root, with Python 3 and clang++ available:

```sh
python3 source/docs/revival/tests/check-split-scroll.py source/docs/revival/tests/r3-before.cpp source /tmp/openttd-scroll-check
```

The test compiles the actual current `DoSetViewportPosition`, `GfxScroll` and 8-bit `ScrollBuffer` bodies into a small framebuffer harness. It compares cached scrolling against a full-redraw pixel oracle. The original r3 function bodies are kept as a baseline fixture. Horizontal, vertical, diagonal and larger-than-view shifts are tested with lower UI obstacles, the upper status bar, and a secondary lower-screen viewport. AddressSanitizer and UndefinedBehaviorSanitizer are enabled. The baseline fails 18 of 20 cases; the fixed source passes all 20 without sanitizer reports. This exercises pixel routing and occlusion, not the emulator or full game simulation, and does not replace a console retest of the user's recording.

## r3b construction controls regression

L (SDL button 5) and A (button 1) share the map click through `N3DSBuildButtons`. SELECT (7) or X (3) switches modes. Y (4) now zooms out; R (6) zooms in. B (2) cancels; START (0) pauses. The UI layout/scaling and r3a renderer are unchanged.

The state regression can be run from the extracted distribution:

```sh
clang++ -std=c++11 -fsanitize=address,undefined source/docs/revival/tests/build-buttons.cpp -o /tmp/openttd-build-buttons
/tmp/openttd-build-buttons
```

It verifies independent/overlapping A/L presses, both release orders, duplicate key events, mode reset and zoom-button isolation. The SDL event path preserves the mouse-click latch when the stylus lifts while a build button remains held. Hardware testing should explicitly include reanchoring the stylus mid-drag and releasing L to commit a road/rail segment.

## r3c mode-sensitive shoulder controls

X/SELECT explicitly selects the control scheme; the selected construction tool does not determine it. In normal tools/windows mode, L zooms out and R zooms in. In map-pad mode, L becomes click/hold, A remains an alternative, R zooms in and Y zooms out. Switching back restores L zoom-out. Y has no zoom action in normal mode.

The shared-button classifier receives `_map_pad`. Switching modes still resets the held-button mask and mouse latch before selecting the new layer, so a shoulder held across the toggle cannot become an unintended build press. Popup-driven returns to the UI also restore normal shoulder behaviour after the final build button is released. Scaling and renderer code are unchanged.

## r3d exit-to-inspection behaviour

Leaving map-pad mode with X/SELECT first calls `ResetObjectToPlace`, before releasing mouse/button state, so an in-progress placement is aborted rather than committed accidentally. It then switches to normal UI input and centres the stored upper-map cursor. The order matters: `SelectN3DSInput(false)` saves the old free cursor position, so centring must happen afterward. The centre is based on the actual upper status-bar top: 200,114 for a 400x240 display with a 12-pixel information bar.

Normal UI touch movement continues to update only the UI cursor. Circle Pad scrolling moves the world beneath the stored map cursor. Normal-mode A clears any active tool before dispatching the map click, allowing station/vehicle inspection even after selecting a tool below. Construction mode retains free stylus positioning and L/A placement; L/R zoom remains normal outside that mode. Scaling is unchanged. Automatic popup returns also centre the stored cursor but retain pending picker/tool callbacks; the explicit X/SELECT exit is the abort action. Normal-mode A cancels a retained tool before inspection.

## r3d automatic AI Debug policy and touch menus

On 3DS, `AIInstance::Died` logs a short company/script diagnostic to boot.log instead of automatically opening AI Debug. The existing AI log remains available through Help > AI Debug. The normal non-dummy AI crash notification is retained, and desktop builds keep their original automatic debug behaviour. DummyAI stops therefore stop stealing the lower screen without disabling AI simulation or hiding genuine AI failure notifications.

3DS dropdowns use a two-tap interaction: tap the toolbar/menu button, lift the stylus, then tap the desired item. Releasing on the parent button no longer executes the default item. X/SELECT closes a pending dropdown before changing control modes. This changes interaction, not scaling, and permits reliable menu access and auditing with both stylus and emulator controls.

## r3d compact menus and one-shot orders

The main toolbar again uses the original 22-pixel row and two switchable pages. Construction toolbars anchor beneath its actual height. Vehicle group windows use a 140-pixel sidebar instead of 200, retaining the vehicle pane and all group commands. Group names truncate before counts. Vehicle details lose five pixels of unused horizontal allowance to fit the 400-pixel logical desktop. Other large dialogs remain audit items.

Orders > Go to requests the lower map-selection pad after the input callback completes. Existing engine tile validation and CMD_INSERT_ORDER perform the actual order insertion. A successful insertion resets placement even when quick_goto is enabled on 3DS, giving one destination per round trip. OnPlaceObjectAbort queues the return; the video loop waits for L/A release before revealing Orders and restoring normal L/R zoom. Invalid destinations keep selection active. B cancels via the existing placement-abort callback. Desktop quick_goto behaviour is unchanged.

The queued picker state must be reviewed for window closure, new dialogs, mode changes and held-button transitions. Emulator and host tests cannot establish physical-console stylus feel or memory stability.

Run the exit regression from the extracted source package:

```sh
python3 source/docs/revival/tests/inspection-exit.py /tmp/openttd-inspection-check
```

It extracts the actual cursor-selection, centring and X/SELECT handler bodies and checks cancellation before release, independent UI/map cursor storage, both toggle buttons, status-bar-aware centring and the title-menu guard with sanitizers.

## r3e native toolbar row

The gameplay main toolbar is 320 pixels wide at logical x=40, with 14 buttons on each of the original two pages. Its 22-pixel strip is copied from x=40 at 1:1 instead of resampling 400→320. Touch input in that strip adds 40 to physical x; input elsewhere retains its prior mapping. Thus sprite proportions and hit areas agree. Dropdowns below the strip remain in the fitted desktop, so their horizontal anchor converts the native button position back to desktop coordinates. The title screen, construction bars, vehicle windows and upper map retain their prior mapping. Icons remain original pixel art, with no added height or second toolbar row.

Rows covered by a foreground dialog temporarily use the regular desktop mapping to avoid a scaling seam through that dialog. The native-strip predicate checks front-to-back window order for this case. The host toolbar regression includes overlapping-dialog and below-toolbar cases. Reproduce with `python3 source/docs/revival/tests/native-toolbar.py /tmp/openttd-native-toolbar`.

The native toolbar was visually checked after loading a disposable Flufingwell copy in Azahar's original-3DS configuration. Both-page geometry and touch coverage are host-tested; physical stylus operation still needs hardware confirmation. The last dialog-occlusion guard is host-tested and compiled, rather than visually exercised through a large dialog.

## r3f shared touch dropdowns and Orders pane

All menus using ShowDropDownList/ShowDropDownMenu get the 3DS layout: a 320-pixel full-width popup at logical x=40,y=22, copied at native pixel proportions. Its row height is the maximum of 22 and the natural height of every item. Drawing, hit testing, scroll capacity and list height use that same uniform metric. Text/sprite content is vertically centred; masked and separator entries retain their semantics. Long lists scroll within the lower display; the scrollbar is 20 pixels wide. Opening is strictly two-tap, with drag_mode=false, so releasing over an entry after opening a popup cannot select it accidentally. Scrollbar hits cannot select a list entry. Non-3DS layout remains the legacy implementation.

Orders for train/road, ship/aircraft and competitor vehicles use a fixed 320×192 pane at x=40,y=22. Six 22-pixel rows replace six 10-pixel rows, with 22-pixel action rows. Widget IDs and engine actions remain unchanged. The corner resize control is hidden and caption dragging stays anchored, preserving native mapping. The foreground Orders pane retains native mapping while a dropdown is open. Existing one-shot station selection and return-on-release remain in place.

Vehicle group/list and details windows have not yet received a native-width redesign. Their dropdown selectors benefit from the shared change, but the main panels retain r3e geometry/scaling. These are the next priority; a groups/vehicles switcher and separate detail sections need a dedicated layout rather than shrinking all content indiscriminately. No claim of a completed all-window scaling audit is made.

Regression recipes from the extracted source root:

```sh
python3 source/docs/revival/tests/touch-dropdown.py /tmp/openttd-dropdown
python3 source/docs/revival/tests/touch-orders.py /tmp/openttd-orders
```

Tests compile actual dropdown layout/hit-test code and apply the actual Orders reflow to all three widget tables with ASan/UBSan. They cover long/short/sprite menus, scrolling, masked/separator entries, scrollbar exclusion, widget bounds, row capacity and fixed pane sizing. They do not replace physical stylus testing or visual checks of all translated/custom content.

### r3f emulator walkthrough

Using a disposable copy of the August 1980 Flufingwell game, native company and Orders loading menus were opened and selected. A long train sorting menu scrolled with its wider scrollbar, stayed open rather than selecting a row on the scrollbar tap, and selected Length correctly after scrolling. Opening an Orders dropdown did not select the option under the opening tap. The enlarged train Orders pane rendered correctly; Go to entered SELECT STATION and B returned to Orders. Successful station insertion was not confirmed in this walkthrough. Stylus-drag automation did not reliably move the map cursor. All four stopped DummyAI companies wrote the expected suppressed-popup diagnostic, without an automatic AI Debug window. Vehicle lists and train details were visually inspected and remain crowded in the prior layout.
