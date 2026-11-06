# OpenTTD 3DS Revival implementation guide

This guide describes the r3d inspection-centre refinement of the r3a repair, based on EnergeticBark/OpenTTD-3DS v1.0.1, OpenTTD 0.7.0. The tested r1b repair and r2 UI prototype are preserved separately. r3 needs independent physical-console validation.

## Build and project layout

The complete source distribution contains `source/` and `environment/`. Start Docker Desktop and run `environment/build.command`. The pinned devkitPro image and package setup are specified in `environment/Dockerfile`; `environment/build.sh` contains the exact configure flags. Source is copied into `/build` inside a disposable container because the legacy configure system does not handle paths containing spaces reliably. Build outputs go into `builds/repair-r3q/`: the `.3dsx`, matching `.elf`, languages, and toolchain inventory. Keep the ELF paired with each distributed binary; addresses from one build must not be resolved using another build's symbols.

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

## r3g optional upper-screen menus and vehicle controls

In normal UI mode, Y transfers the open menu workspace to the upper display at the native 400×240 pixel size. The lower display becomes a relative touchpad. Circle Pad moves the UI cursor; D-pad up/down emits wheel events at the pointer; L/A share click/hold; R scrolls down and X scrolls up. Y/SELECT returns menus to the lower display. B retains cancellation and START retains pause. Y remains zoom-out in construction mode. The toggle is ignored on the title screen, without an open menu, and in map-pad mode.

The feature copies the existing UI surface onto the upper framebuffer at presentation time; it allocates no additional framebuffer and changes no save state or memory budget. Cursor drawing temporarily targets the UI surface; hit testing remains routed to UI windows, so a menu click cannot reach the hidden map. The UI surface is copied using its own pitch and the destination surface pitch, for 400 pixels per row and 240 rows. Returning marks the whole screen dirty to restore a fresh map instead of reusing the overwritten pixels.

The menu that was active when transferring is tracked by window class/number. Closing it returns to the map. Child menus can be used in the upper workspace. Changing from an upper Orders window into station selection restores the map while preserving the pending placement callback, even if L/A is still held; the next click chooses a station. A physical console must still check stylus reanchoring and held-button feel.

Vehicle group lists no longer add the desktop-only 65-pixel train expansion after being sized to 400 pixels. All four group-list types use a 400×204 layout, preserving the groups sidebar, existing drag/drop, commands, sorting and vehicle row counts. The available/manage/start/stop action row is 22 pixels tall; start/stop are 22 pixels wide. Station/shared-order simple lists keep their original narrower layout and 325-pixel train size, which already fits within 400 pixels.

Vehicle details preserve their existing content and tab callbacks. Service up/down are now side-by-side 22×22 targets; train detail tabs are 22 pixels tall. The train window is 184 pixels high and fits beneath the toolbar. The service label truncates safely to available width. The resize corner is hidden in this layout. Base road, ship, aircraft and a representative four-part road vehicle fit the display; unusually long articulated NewGRF vehicles and translated text still need additional checks.

Reproduce new regressions from the extracted source package:

```sh
python3 source/docs/revival/tests/upper-menus.py /tmp/openttd-upper-menus
python3 source/docs/revival/tests/vehicle-layouts.py /tmp/openttd-vehicle-layouts
```

These use actual switching, pointer, button, framebuffer-copy, widget transform and resizing code with lightweight host stubs and ASan/UBSan. Checks cover toggle guards, relative reanchoring, A/L overlap, UI routing state, wheel/buttons, automatic return, placement-preserving handoff, framebuffer stride/bounds at 8/32-bit depth, vehicle widget bounds and 22-pixel action targets.

Emulator walkthrough on a disposable Flufingwell copy: Y transferred the train list, Circle Pad/A opened a train, Y restored the map, vehicle details transferred to the top, D-pad scrolling moved through wagons, and closing details automatically restored the map. No visible map corruption was left after returning. The placement-preserving final handoff is compiled and host-tested; full successful station insertion from an upper Orders window remains a hardware/emulator follow-up. No claim of measured heap improvement or original-console validation is made.

## r3h native bottom-screen vehicle layouts and screen pin

Vehicle group lists, station/shared-order simple lists and details now have screen-specific layouts. The lower panes occupy logical x=40..359 and copy 320 pixels at native proportions; moving upward restores the canonical wider geometry. A 3DS-only virtual OnN3DSScreenChange callback runs on UI windows at the transfer boundary, before repainting. Fixed-size per-window geometry snapshots preserve the canonical layout without cumulative scaling or per-frame snapshot allocation. No extra framebuffer is allocated. The existing native-row renderer/input mapping covers these panes and their vehicle-camera child windows. Camera viewport origins move with the window; oversize cameras are constrained when returned below. Other legacy dialogs still use their previous compatibility scaling.

The compact group window has Vehicles and Groups views. Vehicles use the full row width, with five train/road rows or three ship/aircraft rows. Groups use five 22-pixel rows and retain create/delete/rename/replacement-protection commands. Selecting a group returns to the filtered vehicle view. To move a vehicle into a group below, drag the vehicle onto the Groups button and select the destination from the popup. The pending vehicle ID survives the engine's drag-abort cleanup; the existing CMD_ADD_VEHICLE_GROUP validates the command. The wide upper view retains the original direct sidebar drop targets. Automated UI dragging was unreliable, so physical drag-to-Groups assignment still needs a console playtest.

Compact Details separates Overview and Details. Overview wraps the four existing statistics into bounded 22-pixel rows. Details shows the vehicle/cargo content; trains retain Cargo, Information, Capacities and Total Cargo tabs with eight wagon rows. Service controls remain 22×22, with a wrapped service label. The upper screen restores the combined statistics/content layout. Long translated/custom strings and unusually long articulated vehicles remain follow-up cases. The new section labels are English literals, as in the existing 3DS control pad. The engine's language source and language-pack identifiers remain unchanged, so this stays an executable-only update.

The existing pin on 3DS vehicle list/view/details/Orders windows now requests screen transfer instead of sticky-window protection. Other window classes and non-3DS builds retain sticky behaviour. The pin drawing reflects the current screen state without setting WF_STICKY. Its old sticky tooltip is suppressed on these 3DS windows. Screen changes requested by a pin wait until touch, A/L and mouse-down state have all been released. The request records the desired screen and target class/number, avoiding duplicate toggles and stale pointers if the menu closes. Y remains the hardware shortcut. The Orders pin is restored to the full 12-pixel width.

New test recipes from the source distribution:

```sh
python3 source/docs/revival/tests/compact-vehicles.py /tmp/openttd-compact
python3 source/docs/revival/tests/native-vehicle-rows.py /tmp/openttd-native-rows
python3 source/docs/revival/tests/screen-pin.py /tmp/openttd-pin
```

Actual callback, geometry, row routing, viewport translation, pin dispatch and deferred-request code is compiled in sanitized host harnesses. All four vehicle types fit the compact panes, row grids agree with hit geometry, and twenty screen-switch cycles restore canonical coordinates exactly. Existing upper-menu, dropdown, Orders and cached-scroll regressions also pass. The old vehicle-layouts.py entry point runs the expanded compact layout regression.

Emulator verification on a disposable Flufingwell copy: native train, road, aircraft and empty ship lists; existing road groups; train group creation/filtering; train and aircraft Details; train Information tab; service adjustment 150→160; compact→wide→compact Details; bottom pin transfer to top and upper pin return via precision controls; and native vehicle camera rendering over the compact list. Hardware stylus/group drag assignment, road/ship Details content, custom NewGRFs, translations and longer original-console endurance remain unverified. Original protected saves and SD card were not modified.


## r3i construction and purchase menus

Construction UI now shares the native 320-pixel strip used by vehicle panes. Window-class routing includes rail/road/tram/water/airport toolbars, terrain tools, station/depot/signal/tree selectors, bridge choices, station joining, industry funding and vehicle purchase/depot windows. Narrow selectors are centered within logical x=40..359 without horizontal resampling. Rendering and touch input use the same row-ownership predicate. Unrelated legacy modal dialogs retain their existing fallback.

Construction icon bars use eight columns of 40x32 below, or 50x32 above. Widget IDs and callbacks stay unchanged. Panel spacers disappear; the caption and pin occupy their own 14-pixel header. Rail stations use a 320-pixel two-column layout, with 22x22 track/length buttons, 22-pixel coverage buttons, orientation previews and a separate coverage-text column. NewGRF station selectors use five 22-pixel list rows beside the controls and fit within 218 pixels. The waypoint chooser shows four original previews instead of five so it fits. Airports use two columns of 22-pixel options; availability/disabled-state logic is unchanged. Bus/truck/dock coverage and random-tree actions gain taller targets.

Vehicle purchases use native 320/400 widths and taller action footers. Specification text clips within its own panel and is capped to reserve footer space. FillDrawPixelInfo rebases coordinates, so the temporary info DPI explicitly restores its top coordinate before invoking the existing text renderer. This was verified after an emulator walkthrough caught blank specifications in an intermediate build. Long custom purchase descriptions may still be clipped; this release does not add a scrolling specification page.

Depot initialization sets whole-cell capacities that fit a 320x218 workspace before recording the minimum size. This matters because the original train and aircraft minimum widths exceeded the lower screen. Shared width changes respect cell steps, update capacities through OnResize, and preserve vehicle identities and commands. No additional framebuffer or per-frame geometry allocation is introduced. Oversized custom sprites, manually enlarged windows and unusually long descriptions still need further testing.

The construction pin requests the same release-gated screen transfer as vehicle windows. A missing pin is appended before WIDGETS_END without shifting existing IDs; it adopts the caption colour. Its old sticky tooltip is suppressed. X from an upper map-construction selector returns to map control while preserving the selected placement tool. Y/SELECT return to the lower tools. Other upper menus retain X scrolling. The control pad describes the construction X action.

Reproduce the new layout regression:

```sh
python3 source/docs/revival/tests/construction-layouts.py /tmp/openttd-construction
python3 source/docs/revival/tests/upper-menus.py /tmp/openttd-upper
```

The sanitized harness compiles actual station/airport constructor reflows, construction toolbar layout, depot capacity clamping and the shared screen-change callback. It checks controls stay inside the display, station hit targets are 22 pixels, airport choices do not overlap, custom-station list capacity is five, depot cells fit, and repeated screen changes do not accumulate resizing errors. The upper-menu harness now also checks placement-preserving X handoff. Existing vehicle, pin, Orders, dropdown, station-picker, toolbar and exit regressions pass. Cached-scroll pixel regression still passes 20/20 while the preserved old baseline fails 18/20 as expected.

Emulator: disposable copy of the August 1980 Flufingwell save, Azahar 2126.2. Inspected native rail/road/water/airport/terrain toolbars; standard rail station controls; airport choices with disabled future types; bus/truck stop orientation and coverage; ship depot orientation; dock coverage; trees; available-train list and selected locomotive specifications. Verified station pin transfer, X return to map control, road-selector pin transfer/return, and purchase compact/wide/compact transfer with readable specifications. These checks do not establish original-console stability. NewGRF station/waypoint layouts and all four depot capacities have host coverage but lack a complete emulator/hardware walkthrough. Bridge construction, station-joining flows, industry funding, actual vehicle purchases and lengthy touch-drag construction remain playtest cases. No SD-card writes or original-save modifications occurred.


## r3j management and title menus

The main menu fills a native 320x240 lower workspace. All action buttons are 22 pixels tall; existing landscape sprites retain their proportions. No new artwork or language IDs are needed. The upper title branding is retained. Options opened from the title use the same native rendering, so the background menu remains aligned. The screen-transfer pin is hidden in title mode, where the map workspace is unavailable.

A management-window classifier adds native rendering and existing release-gated pin routing to Company Details, Game Options/Advanced Settings/Difficulty, custom currency, industry and station directories, and industry/station detail windows. Existing narrow detail dialogs are centered without horizontal resampling; they are not comprehensively redesigned here. Company Details uses 320/400 widths, retains the portrait and statistics, and places the four local actions in two rows of 22-pixel buttons. HQ actions sit below the statistics.

Game Options uses a two-column label/dropdown grid. Advanced Settings uses eight 22-pixel rows with 22x22 decrement/increment buttons and a 44x22 boolean target. Drawing and click decoding use the same dimensions. Text can wrap across two lines; long custom/translatable strings may still clip. The scroll bar has a 22-pixel width and the free-resize corner is hidden. The upper workspace expands text width to 400 pixels.

Difficulty retains the existing temporary-settings transaction and Save/Cancel commands. Three pages show six 22-pixel rows each (four on the last page), with footer arrows to move between pages. N3DSDifficultyOption maps hits back to the canonical 18-entry table, skipping the two deprecated slots; out-of-page and empty-row hits return invalid. The old desktop click gap remains unchanged. Nothing applies until Save is used, as before.

Industry funding has five 22-pixel choices, a bounded information area and a 22-pixel Fund button. The industry directory shows eight 22-pixel rows, allowing two lines of production text. Station directories arrange facility filters in a 32x22 row and all active cargo filters in 22x22 cells below it. Up to 32 cargos fit in multiple rows; the remaining space determines whole 22-pixel station rows. Station names and waiting/rating indicators occupy separate text lines. Drawing and hit decoding use the actual list-panel origin; lower and upper layouts retain all cargo-filter IDs. The free-resize corner is hidden on these fixed layouts. X from an upper funding panel preserves the placement tool while returning to map mode.

No additional framebuffer or per-frame layout snapshots are allocated. Widget geometry changes retain IDs and original commands. Existing construction, vehicle and crash-stability changes remain. English language source is unchanged; this remains an executable-only update.

Validation recipes:

```sh
python3 source/docs/revival/tests/management-layouts.py /tmp/openttd-management
python3 source/docs/revival/tests/construction-layouts.py /tmp/openttd-construction
```

The management harness compiles actual reflow callbacks, shared anchoring, widget geometry, title layout and difficulty hit translation using ASan/UBSan. It checks 20 round trips, native bounds, 1/12/15/32 cargo filters, whole row capacities, non-overlapping title actions and every pixel of all 16 valid difficulty rows plus empty/invalid hits. Existing ten host suites and cached-scroll pixel checks also pass. The pinned network-disabled Docker build completes; existing mixed-enum ABI linker warnings remain unresolved.

Emulator checks on a disposable August 1980 Flufingwell copy: Company Details lower/upper/return; station directory and click-to-centre at Farnwell Central; industry directory and click-to-centre; funding-panel choice/specification display; Game Options and autosave dropdown; Advanced Settings folding and scrolling, numeric train limit 500 -> 300 -> 500; all three Difficulty pages and Cancel; and full-height main menu plus Game Options opened from title. The final binary was separately checked at the title screen and on the last Difficulty page: the long city-council label wraps and its value remains visible. Station-row padding also received a final bounds correction. Original-console testing remains pending. Company share/network edge cases, custom industries, all translated labels, complete station/industry detail content and actual HQ/industry placement are not comprehensively validated. Finance tables, company livery/face editors, town directory, NewGRF/AI configuration, map-generation and file dialogs retain their prior layouts and remain candidates for a later pass. No claim is made that every legacy dialog is now redesigned. Protected saves and the SD card were not modified.


## r3k remaining gameplay dialogs and menu scrollbars

Remaining ordinary gameplay dialogs use a native-pixel workspace. The original text, sprites, graphs, widget IDs and callbacks are retained. The shared route covers 47 remaining window classes, including finances, company colour/face editors, town view/authority, graphs and legends, performance/league tables, subsidies, small map/extra viewport, signs, messages/newspapers, music controls, refit/timetable/replacement, save/load and query dialogs, transparency, AI utilities and networking dialogs. Network functionality itself is unchanged. This is a shared layout/accessibility pass; their internal controls retain the original sizes. Existing dedicated vehicle, construction and r3j management layouts stay in place.

Several unrelated dialogs share WC_GAME_OPTIONS. N3DSUsesScrollableWorkspace therefore checks an explicit per-window n3ds_native_layout flag as well as the class. Company/industry/station/settings reflow callbacks opt into their dedicated layout; NewGRF, AI configuration and message options receive the shared workspace. Narrow station/industry detail and custom-currency dialogs also gain the shared size/scroll handling when needed. Console/chat overlays, main game surfaces/toolbars, dropdowns and title/world-generation screens retain their separate handling.

Oversized menus get an outer horizontal scrollbar along the bottom and, when taller than the workspace, a vertical scrollbar at the right. Arrows move by 64 horizontal or 48 vertical pixels. Clicking the track pages by the visible extent. The thumb can be dragged and updates the menu during the captured touch gesture. Home resets both offsets. Original list scrollbars still scroll entries inside the window; the outer bars move the entire dialog so its hidden controls can be reached. On the upper screen, the outer bars remain on the lower touchpad. Y/SELECT returns the menu below. A screen-transfer pin is added when the header has space; existing header buttons such as a graph's Key or a face editor's toggle are preserved. Y works where a new pin cannot fit.

The lower viewport is 320x196 logical pixels (starting at logical x=40,y=22), or 298 pixels wide when a vertical edge bar is present. The upper workspace is 400 pixels wide. Window dimensions and widget coordinates remain canonical; only the window origin changes. Offset clamping accounts for view size and live changes in dialog dimensions. Viewport origins translate with their owning window. Native strip rendering and touch hit mapping share the same window predicate. A dynamically shortened company-colour window repositions its pin within its current width. Newspaper slide-in animation yields position control to the workspace; normal news duration/closure remains unchanged.

Scrollbar gestures are intercepted before engine mouse-down dispatch, preventing clicks on hidden buttons beneath the bars. Arrow/page/Home requests wait for touch release. Captured thumb drags update absolute offsets without setting the engine's left-button state. Requests remember the front window's class and number and are discarded if it closes or another dialog becomes frontmost. Guards reject title/map mode and concurrent A/L clicks. No new framebuffer or whole-window bitmap is allocated: the existing UI surface clips/repaints the visible content. Each window stores two offsets and a flag.

Town Directory has a dedicated full-width layout with six 22-pixel rows, larger sorting buttons, a 22-pixel list scrollbar, and a population footer. The resize corner is hidden. Drawing and row hit decoding use the same list origin and row size. The existing sort and click-to-centre callbacks remain.

Reproduce the new sanitized regression:

```sh
python3 source/docs/revival/tests/canvas-menus.py /tmp/openttd-canvas
```

This compiles actual window routing, scroll geometry, anchoring, captured-drag handling, drawing bounds and town layout. It checks 47 routes, 360 size/pan/viewport combinations, shared settings-class selection, dynamic pins, horizontal/vertical drag endpoints, arrows/page/Home behaviour, release gating, invalid front windows, mode guards and news-position ownership. The eleven previous host suites and cached-scroll 20/20 checks pass. Docker compilation completes with the existing mixed-enum ABI warnings still present.

Emulator checks used a disposable August 1980 Flufingwell copy. Verified finance small/expanded views, horizontal/vertical edge-arrow movement revealing the final year and loan actions, Home, pin transfer and return; operating-profit graph panning and Key access; legend company selection affecting graph lines; world map rendering and map click-to-centre; company colour editor and the taller train-livery list; dedicated Town Directory and correct Darnwell row selection. The final shared-class build was checked with NewGRF settings: outer vertical scrollbar exposes its bottom controls. No NewGRF changes were applied. Automated native dragging was unreliable, so thumb dragging is host-tested but still requires a physical stylus playtest. Every individual dialog, custom content, translations, network states and original-console performance/stability are not exhaustively validated. Original saves and SD card remain untouched.


## r3l dedicated file browser and compact news

The previous shared gameplay workspace left the title-screen file browser at its legacy dimensions. SaveLoadWindow now supplies its own fixed native layout in title and gameplay contexts. Its constructor applies the layout before first paint, and the recurring layout pass includes dedicated native windows regardless of class or game mode. Native rendering, pointer mapping and title cursor handling recognise the explicit layout flag. N3DSUsesScrollableWorkspace excludes all dedicated layouts, including classes otherwise assigned to the shared workspace. This also retains the dedicated Town Directory without outer scrollbars.

Load/save dialogs use a 320x218 lower pane and 400-pixel width above. Sorting controls, Home, the list scrollbar, filename field and action buttons are 22 pixels tall/wide as appropriate. The path/free-space panel occupies two text lines. Load Game has seven 22-pixel rows; scenario/heightmap loading has six and retains its content button; saving has five plus filename and Save/Delete controls. The resize corner is hidden. The renderer and hit decoding use the same panel origin and 22-pixel step. File ordering, directory traversal, loading/saving/deleting commands and pause handling remain the existing engine paths. No Save/Delete action was used during the UI walkthrough.

NewsWindow has a dedicated native-width card for all three display modes: normal 320x218, thin 320x164, small 320x128; the optional upper view uses 400-pixel width. Cards anchor to the bottom of the screen and require no outer workspace scrolling. Newspaper dates/text use the current width instead of hard-coded 430-pixel coordinates. General headlines wrap above the camera; compact message text has a bounded area below it. Company-news headlines wrap around the close target, and the portrait/name are repositioned to fit. New-vehicle news retains its width-aware callback and has more vertical room.

News camera views resize to the available card area. Physical viewport origins follow the card, virtual dimensions follow zoom, and scroll/destination/current positions shift by half the dimension difference to retain the same world centre. The legacy slide animation continues to yield to explicit native positioning. Message click-to-location and normal lifetime/closure logic remain intact. Very long translated/custom headlines and new-vehicle specifications still require hardware/content testing.

New regression:

```sh
python3 source/docs/revival/tests/file-news-layouts.py /tmp/openttd-file-news
```

The sanitized actual-code harness checks all five file modes, title/game contexts, 22-pixel targets/whole rows, all news modes with/without a viewport, and twenty screen-switch round trips retaining viewport centre. The twelve earlier suites also pass. Cached-scroll checks continue to pass. The pinned Docker build completes with the existing mixed-enum ABI warnings.

Emulator walkthrough: title Load Game occupies native lower width; opening the autosave directory and Home reach the correct paths; selecting the disposable Flufingwell file loads it; the matching in-game Save Game pane shows its filename and action row. News was previewed with a synthetic raw-string industry story over a disposable save in a separate test executable; its thin card/camera fits, and clicking the story centres the main map. A naturally generated subsidy newspaper also wrapped within the full lower card. The fixture source and executable remain outside the corresponding-source release and update ZIP; the release executable has no synthetic news hook. Original protected saves and SD card remain unchanged. Original-console validation and unusually long/custom news remain pending.


## r3m scenario editor and New Game forms

The scenario editor now uses the same native UI rendering, touch coordinate mapping, menu pin transfers, shared scrolling workspaces and construction handoff as normal gameplay. SDL/window routing guards admit GM_EDITOR as well as GM_NORMAL; the title guard remains separate. Found Town joins the map-construction window classes, so X can return an upper-screen town picker to the map while retaining the placement tool. No new screen buffer, graphics cache or audio allocation is introduced.

ScenarioEditorToolbarWindow supplies a native 320x22 single-row toolbar with two pages. Page one has pause, speed, options, scenario files, map, zoom, terrain, towns, industries, roads, docks and trees. Page two has signs, music, help and the starting-year controls. The existing switch sprite occupies the final button. Original widget IDs and action callbacks are retained, unused spacers are hidden, and the legacy desktop resize calculation is bypassed on 3DS. Date painting honours page visibility. Null legacy callback slots are rejected safely.

The editor land-generation panel is 320x164 below (400 pixels wide above), with seven 32-pixel-high tools, enlarged brush controls, a centred brush preview and 22-pixel New World/Reset buttons. Found Town is 320x206 below/400x206 above, with 22-pixel actions, four size choices, City and five road-layout choices. Existing dedicated industry and tree pickers and native road/dock toolbars are retained; settings/list/other shared dialogs now receive the editor routing that was previously limited to gameplay.

CreateScenarioWindow has a fixed 320x218 form with the original four climate sprites, 22-pixel map-size/date/height controls and two 32-pixel world-creation actions. GenerateLandscapeWindow (also used by New Game) has three fixed 320x218 pages: World (climate, map size, date, snow line, seed), Terrain (towns, industries, tree algorithm, generator, terrain, sea level, smoothness), and Borders (all four named edges and border mode). The heightmap variant uses two pages and keeps filename/dimensions on World. Generate remains visible on every page. Switching pages only changes widget geometry/visibility, preserving the settings and original generation/dropdown callbacks. Hidden seed fields neither paint nor consume edit-box input. Page captions are English literals, avoiding changed language-string IDs. Generation progress uses native width, centred text and a 22-pixel Abort target.

Regression test:

```sh
python3 source/docs/revival/tests/scenario-layouts.py /tmp/openttd-scenario
```

It compiles the actual reflow methods with ASan/UBSan and checks all controls are reachable across pages, visible widget bounds, minimum 22-pixel targets and twenty repeated lower/upper/lower layout calls in title/editor modes. Existing route tests now explicitly exercise editor toolbar recognition, screen-pin dispatch and upper-menu entry; the file-browser test includes editor mode. All fourteen host suites and the twenty-case cached-scroll oracle pass. The pinned Docker build succeeds with the pre-existing mixed-enum ABI warnings. Physical-console verification remains required.


Emulator walkthrough (Azahar 2126.2, disposable r3m profile): all three New Game pages render at native width; changing Terrain via its enlarged dropdown persists the selection. Scenario-editor startup creates an empty map. Terrain brush size changes, header-pin upper transfer and Y return work; Create New Scenario shows the larger climate/map/date/height controls. Town Generation renders all choices; selecting New Town, X, A and X places a town in the temporary map and returns to its picker. The editor toolbar switches pages and its forward-year arrow changes the displayed year. The editor industry list includes Many Random Industries and a scrollable list. Both map dimensions were changed to 64 through the native dropdowns, Random Land opened the shared generator and Generate completed a new 64x64 hilly editor map. These are UI/function checks, not a memory stress test or original-console stability result. Heightmap pages have host layout coverage but were not exercised with an actual heightmap in this emulator pass. Original saves and SD card were not written.

A title-screen difficulty-change message still uses the existing small legacy notice layout; it temporarily changes the fitted background presentation while visible. The New Game form returns to native scale when the notice closes. This does not alter the selected difficulty or terrain. Dedicated confirmation/text-entry/notice layouts and unusually long translated labels can receive a later UI pass.


## r3n bounded WAV music prototype

See WAV-MUSIC.md for file naming, accepted formats, installation, buffer ownership, worker lifecycle, diagnostics and test reproduction. The PCM source ring is 64 KiB; a joined background reader adds a 16 KiB stack plus runtime overhead. The prototype shares the SDL sound callback with effects and requests 22.05 kHz output; it preserves the sample's playback duration. `source.list` registers the new music driver, `music.cpp` uses `.wav` names only on 3DS, and SDL startup propagates the actual output rate into the effects mixer. The silent driver remains the fallback when audio initialization fails.

The first prototype refilled in MusicLoop and completed a title-screen loop without underruns, but loading the disposable Flufingwell game caused 479 underrun callbacks. That observation motivated a bounded worker rather than a larger track buffer. Final emulator results are recorded in the r3n validation report. Source/ASan/UBSan/TSan tests cover the final threaded implementation. The supplied soundtrack sample is private update data and is excluded from the GPL corresponding-source archive. All earlier UI/stability changes remain in this source.


Final r3n emulator verification: the background reader completed/restarted the full theme with zero underruns, loaded a disposable Flufingwell copy while streaming, continued into the next month and created its monthly autosave with zero recorded underruns/I/O errors. Jazz Jukebox Stop/Play succeeded. See WAV-VALIDATION.txt for exact scope and limits. No original-console performance or audible-quality result is claimed.


## r3o first-install autoplay and complete soundtrack mapping

MusicFileSettings adds N3DS-only wav_autoplay_initialized, registered under _music_settings with the S flags (SLF_SAVE_NO | SLF_NETWORK_NO), default false. The actual WAV driver's startup probes the existing bounded reader until it finds a supported loose track. It then enables playing, selects All once and marks initialization. No usable audio/track leaves settings untouched; an initialized configuration preserves a later Stop or custom playlist. Config files are saved by the engine's ordinary normal-exit path. No standalone marker file or config replacement is used.

All 22 user-supplied WAVs are ordinary 44.1 kHz stereo 16-bit PCM, mapped by exact title to the engine's nonsequential gm_ttNN names. The supplied files have no duplicate hashes. The actual reader streamed all 22 to completion, producing 103,633,824 output frames at 22.05 kHz with the same fixed ring. Existing audio lifecycle/ASan/UBSan/TSan checks pass, with new missing-track/audio, first-install autoplay, preserved Stop and playlist cases. See the r3o validation report for emulator verification. The soundtrack is excluded from the corresponding-source archive.


The r3o emulator started music from an old playing=false/custom-playlist configuration, loaded a disposable Flufingwell copy, advanced from the theme to Easy Driver, accepted Next to Little Red Diesel and Stop, and saved playing=false plus wav_autoplay_initialized=true on normal Exit. No recorded underruns/I/O errors. This is separate from the complete 22-track host read-through; see WAV-VALIDATION-r3o.txt for limits.


## r3p sound effects and channel publication

The public-release-derived development data contained a zero-byte sample.cat. The existing SoundInitialize function returned success while all 73 allocated catalogue slots remained size zero, so music output alone did not prove effects. A compatible OpenSFX-derived sample.cat supplies the effects without loading the entire bank into RAM. Current upstream OpenSFX uses modern offset flags and 16-bit samples; the documented offline conversion retains ordering/credits and produces canonical mono unsigned PCM8 WAV entries at 11025 Hz. The result is 1,661,236 bytes, 73 slots with 71 nonempty effects, largest PCM 44,654 bytes. The two unused upstream slots stay empty.

StartSound now reserves an inactive channel under the SDL audio lock, reads/allocates its sample outside the lock, sets its source/volume while inactive, and publishes active under the lock. This orders channel fields against the callback and prevents reservation racing callback sample release. The eight-channel mixer and existing sample auto-free remain unchanged. Worst-case sample storage for eight copies of the largest effect is 357,232 bytes plus channel/allocator metadata; the whole 1.6 MB bank is not cached. SDL initialization and WAV music streaming remain the r3o implementation.

sound-effects.log records usable catalogue size and the first eight effect launches. No logging or SD reading was added to the audio callback. The host test compiles the actual CAT parser, SetBankSource/StartSound, index/volume mapping and complete mixer. It verifies all 71 effects mix to nonzero output with correct rate/format, samples are released, and 3,000 main-thread triggers against the callback pass ASan/UBSan and TSan. The Docker build succeeds with the pre-existing mixed-enum ABI warnings.

```sh
python3 source/docs/revival/tests/sound-effects.py /tmp/openttd-effects /path/to/sample.cat
```

Converted audio is CC BY-SA 3.0 and separate from the GPL game code. Attribution, upstream licenses, original download checksum, per-effect credits and the conversion recipe are included. No original TTD effect samples are distributed. See OPENSFX-CONVERSION.txt for asset reproduction. Original-console audible validation remains required.


The final r3p emulator loaded 73 slots/71 nonempty effects and logged world-effect launches with different IDs, nonzero sample sizes and viewport panning during copied Flufingwell simulation. Music continued with zero recorded underruns/I/O errors. Automated tests do not assess speaker sound quality; this remains an original-console check. See SOUND-EFFECTS-VALIDATION.txt.


## r3q train workshop and bounded window dragging

Train depots use a native 320x192 lower pane (four 28-pixel consist rows) or 400x220 upper pane (five rows). Each row keeps an engine/wagon count above the sprites. Counting follows GetNextUnit, so articulated parts and rear dual-headed parts do not inflate the wagon count. The old length metric is explicitly labelled Len and is separate from this count. Horizontal scrolling moves the train sprites without hiding the count.

Train purchase windows use four 22-pixel list rows, a bounded details region and full-height Build/Rename buttons. Row selection uses the same 22-pixel stride as drawing. Tapping details scrolls statistics that exceed the region, without growing the window.

Pin on a train depot or its associated purchase window toggles the depot alone onto the upper screen. The purchase pane remains below; the map returns above when unpinned. X, Y or Select toggles DEPOT CONTROL: the lower screen becomes a touchpad for the upper depot, Circle Pad moves its pointer, A/L clicks and holds, and D-pad up/down scrolls. Toggling back restores shopping. Pointer and held construction state reset on transfer. Other pin-enabled windows retain their whole-workspace upper-screen behavior. Only one train depot is paired at a time.

N3DSTopWindow is the shared authority for rendering, hit testing, occlusion and cached scrolling. The paired depot uses the existing map framebuffer; no third framebuffer or second simulation is allocated. Toolbar occlusion and lower-window activation ignore the upper depot. Cached viewport scrolling treats its rectangle as an obstacle, so world pixels cannot overwrite the depot. Native windows can be dragged by their caption within their physical screen bounds; their position persists until a screen transfer. Full-screen panes have little or no movement space; pinned depots stay anchored. Drag snapping ignores windows on the other physical screen.

Reproduce the actual-code sanitizer test with:

```sh
python3 source/docs/revival/tests/train-workspace.py /tmp/openttd-trains
```

It checks 20 repeated screen round trips, widget/action bounds, every pixel of purchase selection rows, paired input/draw ownership, focus guards, retained manual positions and articulated/dual-headed consist counts. The existing fourteen UI suites pass. The depot cached-scroll oracle passes 30/30 cases (r3p fails 8); the original split-scroll oracle passes 20/20 cases. Existing mixed-enum linker warnings remain. This is a UI repair, not proof of original-console memory/performance stability. The separate validation report records emulator scope and hardware checks still needed.
