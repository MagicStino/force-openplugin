# Catalog thumbnails — static PNGs

The manager loads normal bundled PNG thumbnails through the native Force skin. About 200 catalog entries share one thumbnail file per entry across the three visible rows. New or missing artwork uses a neutral blue-grey gradient. Titles use the existing 580-pixel field with a conservative font-width budget and UTF-8-safe ellipsis; full catalog names remain in the underlying metadata.

The former live pixel grid is removed: no 5,400 image parameters, no palette cells, no image automation callbacks, and no runtime screenshot download or decoding worker. Force caches skin PNG files; online replacement is intentionally not attempted. Refreshing the catalog still updates plugin metadata. Artwork updates ship with a matching manager/skin package.

On the test Force, removing only the image widgets still took approximately 26 seconds to load. The owner reported approximately 0.5 seconds after the diagnostic build removed the 5,400 parameter block. The complete STORAGE build now exposes 228 functional parameters. Hardware acceptance of the complete build is tracked in the startup diagnostic notes.

## Compatibility

The new binary and skin must be installed together. Every functional parameter ID matches the previous STORAGE development build; only trailing pixel/ready parameters were removed. The much older firmware manager placed remote controls after the pixel block; saved automation for that older layout is not migrated by this update. Remove and re-add old Plugin Manager instances rather than reusing their saved automation. Other instrument plugins and their saved state are unchanged.

## Validation

Build-time guards reject pixel controls and parameter counts above 255. Tests cover known/unknown thumbnail IDs, repeated skin generation, UTF-8 title clipping, catalog parsing with unknown-artwork entries, and zero pixel callbacks during wrapper processing. UI verification covers CATALOG, FIND, REMOTE ACCESS and eight STORAGE states.

## Follow-up: persistent missing-image downloads

Requested by owner: download only missing artwork, persist it, and use normal PNG loading on a later manager/application launch. Do not reintroduce pixel parameters. Keep downloads off the startup path, use bounded HTTPS downloads/decoding and atomic files, deduplicate retries, and retain a gradient when offline or invalid. Existing image slots and new catalog IDs need distinct handling: new IDs require adding/remapping native skin slots. Force's skin cache may require an application restart, so do not promise visibility on merely closing/reopening the manager until measured. Promote only a complete validated image/slot mapping; retain the previous usable mapping on failure. This follow-up is planned, not implemented by the static-PNG build.

## Readability follow-up

Owner confirmed the complete PNG build opens quickly and works. A separate layout build increases description size from 21 to 32 (approximately 1.5×), allocates two 26-pixel lines, and uses font-width-based UTF-8-safe wrapping with an ellipsis. The leftover Stable/tested badges are removed; Beta, CPU and Legacy badges are placed beyond the description field. Titles remain to the right of the thumbnail. The Nova Audio gradient preview and all eight STORAGE views pass render verification. This follow-up is prepared separately and not hot-deployed during the owner's storage-copy test.

### Catalog navigation and branding — 2026-11-06

The strip below the three cards now contains A–Z / Z–A sorting and letter-group
navigation. A group expands to individual letters; selecting one sets the actual
paginator to the page containing its first matching plugin. Filters and search
remain applied. The Back button returns to the groups. Empty groups/letters are
hidden. Leading display tags such as `[SYN]` do not affect alphabetical order.
Sorting rearranges only view indexes, preserving queued package identities.

Optional Popular uses non-negative integer `downloads` or `download_count`.
Newest and Oldest use plugin `updated` / `updated_at`, falling back to `date` /
`published_at` of the selected compatible release. Both directions keep unknown
dates last; alphabetical order breaks ties. Controls are hidden when the filtered
catalog has no applicable metadata. The bridge previously dropped upstream update/download metadata. The local
catalog now preserves available dates for 204 of 208 entries; undated entries
remain unknown. Publish that catalog alongside the manager update to
make these controls available online. No creation date is inferred from testing
dates or the catalog generation timestamp.

The package and generated plugin now use OPENPLUGIN MANAGER, manufacturer
OPENPLUGIN, folder `OPENPLUGIN - VST - OPENPLUGIN MANAGER`. UID PlMg / 506c4d67
and package ID openplugin-manager are unchanged. Upstream legal attribution and
historical recovery instructions retain their original names. Package testing
covers upgrading from the old branded built-in manager without duplicate UIDs.
The navigation build has 256 parameters (Oldest appended without shifting existing IDs), with the original 228 kept in place.

Touch follow-up: letter readouts now pass mouse presses to the entire button
underneath. Display-only label/availability feedback is rejected by the action
whitelist; previously it could be misread as a press on slot zero. Group selection
immediately jumps to the first matching entry, then exposes exact letters.
Groups A-D through Q-T expose only four letters; U-Z exposes six. This fixes
stray Q/R buttons appearing outside M-P. Regression tests cover all 26 letters,
immediate group pages, hidden out-of-group slots, and repeated display echoes.

Hardware follow-up: setting ignoreMousePresses on the readout container did not resolve physical-touch reliability. Letter/group/Back labels are now baked into ordinary button PNGs, exactly like A-Z and Z-A. Per-slot artwork selection reuses the existing label parameter IDs; no extra parameters are added. Only one enabled button occupies each slot. The user confirmed that a leading space in the registered display name places the manager at the top on this Force; the installed test registration preserves that prefix without renaming its folder or changing UID.

The binary product name must remain PLUG_NAME while the skin retains its existing
identity. Changing it to the leading-space display name caused a reported missing
skin on Force. Chooser metadata can retain ` OpenPlugin Manager`; the header
rename is deferred until a matching skin identity is tested.

### Matching title-case identity
The corrected build uses binary product name `OpenPlugin Manager` and matching
skin folder `OPENPLUGIN - VST - OpenPlugin Manager`. The chooser alone adds a
leading ASCII space through plugin metadata. UID is unchanged. Package upgrade
tests verify the matching folder, display name and single registration.

Popular, Newest and Oldest hide all alphabet groups, individual letters and
Back/refine controls. A–Z and Z–A restore them. Hidden jump actions are ignored.

Sort buttons are grouped by color: A–Z/Z–A blue (#263c50), Newest/Oldest
brown (#493c32), Popular orange (#59402c), all with light centered text.
Alphabet groups, individual letters and Back use lighter blue (#354a5c).
Back is slightly darker (#233d53) than the letter buttons.
All sort labels use 25px text; letters/Back 28px. Light text (#e9edff)
has at least 7.89:1 contrast against every navigation button background.

The # button is omitted. Alphabet groups and Back/refine rows begin at x=552,
leaving a 32px gap after Popular; the U–Z refinement still fits through x=1244.
Legacy parameter/option IDs remain stable.
