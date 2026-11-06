# Gameplay menu coverage — r3k

| Menu family | Handling |
| --- | --- |
| Vehicles, construction and previously adapted company/settings/station/industry panels | Existing dedicated native layouts retained |
| Town directory | New 320/400-pixel layout; six 22-pixel rows and larger sorting/list controls |
| Company finances, colour schemes and manager faces | Native content; edge scrollbars for hidden portions; upper view |
| Town details and local authority | Native content; edge scrollbars when needed |
| Graphs, legends, performance and league tables | Native graph/table proportions; edge scrollbars; Key and other header controls preserved |
| World map, extra viewport, signs and land information | Native rendering and viewport translation; edge scrollbars as needed |
| News, history, message options, subsidies | Shared native workspace; news animation yields position control |
| Timetables, refit, replacement, waypoint details and previews | Shared native workspace |
| Save/load, text entry, confirmations and on-screen keyboard windows | Shared native workspace; existing commands retained |
| NewGRF and AI configuration/debug | Shared native workspace, including settings-class variants |
| Music controls, playlists and transparency | Shared native workspace; existing audio capabilities unchanged |
| Network/client/password/status dialogs | Shared layout route; original networking availability unchanged |

Oversized windows have horizontal/vertical edge scrollbars with arrows, page clicks and draggable thumbs. Home restores the upper-left content. Inner list scrollbars continue to scroll their entries. The optional upper-screen workspace remains available with Y or a pin where the header supports it.

This table records source coverage, not exhaustive interactive validation. The implementation guide records the emulator walkthrough and test limits. Original small internal controls remain in many dialogs; precision controls on the upper screen can be used. Console/chat overlays, dropdowns, title and generation/progress screens keep their existing separate handling. Hardware stylus dragging and a broad console playtest remain pending.
