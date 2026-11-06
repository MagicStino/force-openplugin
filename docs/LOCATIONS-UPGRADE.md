# Plugin Manager STORAGE test build

STORAGE lists Internal and mounted SSD, USB and SD-card destinations with their actual labels and free space. A short **Move here** button appears inside each usable alternative's row. More drives opens the next three rows. Unsupported drives remain visible with the reason moving is unavailable. **Repair plugin skins** remains available whenever the manager is idle, including for users whose skins never worked.

## Moving and reclaiming Internal space

Save the current project before confirming a move and application restart. The manager checks its installation history, package manifests, registered plugin IDs, available space, links and stored paths. Only verified manager-owned VSTs qualify. Official content, add-ins, manually installed plugins and the manager itself are excluded. Packages that require symbolic links remain on Internal when moving to the external executable view.

The operation copies complete package folders, flushes each completed package together, compares contents and updates supported XML preset paths. It registers the destination binaries and skin search root. After the destination copies are verified, it replaces each moved Internal folder with a compatibility link, verifies the retired original against the destination again, then deletes that original data to free Internal space. Failed verification preserves the remaining copies and recovery journal. The compatibility links themselves consume negligible space and allow existing references to the old path to continue resolving.

Use **Move here** on the Internal row to copy back, verify, and switch registrations to Internal. This copies current drive content, including new presets. The external copies are retained for recovery/reuse. Existing destination copies are reused only when a recorded move plan proves their origin and their complete contents match; conflicting content is never overwritten automatically. A retry can reuse complete verified copies from an interrupted move. No operation restores an entire old preferences file.

The selected destination becomes the manager's new-install preference, separately from the Force Activations preference. Link-free new packages use it; packages requiring links use Internal. If the selected drive is unavailable, installation is blocked rather than silently redirected. Without a manager selection, the existing Activations preference and Internal fallback apply.

## Drive execution and missing drives

Discovery runs outside the audio/UI polling thread. It checks writable storage, stable UUID identity and executable mapping capability using one temporary 4 KiB file per usable destination. It does not load every plugin or read every file's contents during discovery. Full content verification is reserved for a requested move.

External plugins use `/run/openplugin-volumes/<UUID>/Synths`, a dedicated executable view of `<drive>/.openplugin/Synths`. The user's normal drive mount is not remounted or formatted. The view retains nosuid, nodev and nosymfollow. Missing drives produce a reconnect message; reconnect and move plugins elsewhere before routinely removing that drive. Reopen the manager or use Refresh drives after connecting/disconnecting storage.

The image payload installs `runtime/25-openplugin-volumes.conf` before acvs startup. The helper and drive records remain on Internal under `/data/openplugin/locations`. Startup recreates views with a bounded wait and never installs into an empty mountpoint. Older images without this hook cannot offer external moves. The standalone manager ZIP alone does not install this system hook.

**Current development deployment:** the hook is temporarily under `/run/systemd/system` because the test Force firmware is read-only. It disappears on reboot. Return plugins to Internal before rebooting this test setup. The permanent image hook still needs a physical reboot test; no firmware has been flashed.

## Plugin skin repair

Successful installs/updates register skin search roots once per batch before restart, including when a later package fails. Moves register the destination root. Opening/refreshing the manager checks for missing roots. It cannot intercept another plugin's load callback, so it does not rewrite active MPC preferences on every plugin load.

**Repair plugin skins** performs a read-only check first. It offers repair and restart only when a root is missing, preserves existing roots and unrelated preferences, and backs up settings. If search roots are already correct, it explains that; absent skin assets require reinstalling the affected package. Repeated repair is safe. There is no Undo last repair button because later installations may depend on the added roots.

## Progress and recovery

Move/repair progress shows the current stage and plugin. The critical debug log is capped at 8 KiB; file-by-file and background discovery messages are excluded. View debug log shows one event at a time for photographing. Each move keeps a `MPC.settings.move-recovery-*` journal beside settings. COMMITTED records registration commit; RECLAIMED records completed Internal cleanup. Preserve these records if an operation fails.

The standalone progress screen supports the tested Force display. MPC Gen1 display support is not claimed. Remote access remains device-wide across sessions, with the applicable enable/disable action and IP, port and login hint.

## Validation and limitations

Automated tests cover ownership, conflicting destinations, interrupted copies, settings preservation, skin repair, copy-back of new/updated content, link-dependent install routing and UI action guards. Generated skin previews check seven screen states, touch bounds and functional control IDs. Actual Force tests confirmed SSD executable-view creation/restoration and JV-880 ROM audio. The full cleanup/return test result is recorded in the deployment handoff.

Complete-folder copies include manager-installed JV-880 ROMs. Third-party code may use external content or runtime paths the manager cannot inspect. Detected unsupported absolute references are excluded; this does not prove compatibility with every third-party plugin or saved project.

## Deferred: catalog sources

Add a later Sources tab showing configured catalog URLs and allowing changes. Validate candidate catalogs before saving, preserve working configuration on failure, and offer default restoration. This is deliberately outside the current storage test build.

Move checks now show a grey, non-interactive **Calculating...** indicator in the selected drive row immediately after tapping Move here. The screen explains that plugin files and available space are being checked. Confirmation appears after those checks finish. **Go back** restores the available Move here buttons. No files move during calculation.

## Next image build: update the online guide (user request, 2026-11-06)

Pending release task: update the online guide when building the new firmware image. Do not treat screenshot preservation as publication or mark this complete before the guide is updated.

- Use the preserved captures and provenance in `website/assets/screenshots/2026-11-06/`: full catalog with 208 indexed, filtered catalog, queued installation with Continue, STORAGE, and Remote Access. The USB DRIVE marketing image is an edited derivative; retain the original MUSIC capture.
- Explain queued installation → Continue, STORAGE drive rows and free space, Calculating → confirmation → Go back, and Repair plugin skins.
- Document verified Internal cleanup, keeping link-dependent plugins Internal, copy-back, new-install destination selection, and reconnecting missing drives.
- Build the permanent acvs startup hook into the image and validate a physical reboot before describing external plugin storage as reboot-persistent. Replace the current temporary-test caveat only after that validation passes.
- Check captions and availability claims against the final image, preview the guide, and publish the updated guide alongside that image release using the website deployment workflow.

User asked to keep this tied to the next image build; no separate scheduled reminder is required.

### Live storage progress (2026-11-06)

Preparation and drive/skin checks now run with a worker-side progress reader.
The STORAGE header shows the current phase/plugin and elapsed seconds; the next
line shows plugin/file counts and the end of the current relative filename.
Snapshots are throttled to 500 ms and isolated per manager instance, so overlapping
previews do not overwrite each other's progress. Parameter display callbacks only
read memory. No per-file history is added to the bounded critical debug log.

Copying, verification, drive flushes and cleanup retain their existing safety
checks. The standalone move display now shows elapsed time and a current filename
as well as copy totals. An advancing timer is not proof that disk I/O is advancing.
Preparation remains a full path-safety/content check; it is not replaced with a
weaker size-only check. On the test Force the preparation-only run completed with
52 movable plugins, one staying in place, and over 31,000 visited entries. Another
old-manager preview overlapped this run, so its 32.5 seconds is not a clean timing
benchmark. No plugins were moved by this test.

Validation: 30 storage helper/UI tests passed, including preparation progress,
settings remaining unchanged, and isolated concurrent snapshot paths; ARM build
succeeded with the existing 228 parameters. Live application reload is still
needed to verify the new progress text on hardware.

Drive discovery correction: only direct mount points under `/media` qualify as
external drives. Nested mounts (including propagated development bind mounts
inside `/media/az01-internal`) must never appear as move destinations. This filter
also applies to executable-view restoration and install-target discovery. The
reported extra `poloq - VST - Plugin Manager` destination came from such a nested
test bind mount, not a physical drive.

Queued installs, updates and removals intentionally block plugin moves. Storage
shows “Finish pending plugin changes first.” and directs users to finish
the install/update in Catalog and restart when asked. Move here stays visible
as a grey, inert control for otherwise viable destinations. Existing missing-drive
warnings retain priority. Drive visibility remains unchanged, including small
or unidentified removable media.
