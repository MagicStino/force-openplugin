# Plugin Manager startup investigation — 6 November 2026

## Confirmed

After reboot the original manager is active, with no STORAGE tab. User still reports approximately 20 seconds to load. No new manager deployed during this investigation.

Active binary SHA-256: `4f7958fc50a925031f9ad3639822bfd12c4aae18b09a2b8f394b36b13fc4f314`.
Path: `/usr/share/Akai/Content/Synths/poloq - VST - Plugin Manager/plugin_manager.so`.
No openplugin test mounts appeared in the post-reboot mount listing. Application PID 382; uptime approximately 9 minutes; load average 0.21 / 0.72 / 0.43.

## Measurements on the Force

| Measurement | Result |
| --- | --- |
| Original binary dlopen | 0.001573 seconds |
| VST instance creation | 0.000338 seconds |
| effOpen | 0.000001 seconds |
| Read all 5,571 parameter names, labels, displays and values | 0.014123 seconds first pass; 0.007632 / 0.007730 repeats |
| First isolated engine startup | Still loading catalog after 20-second observation window |
| Second isolated engine startup | Catalog ready at 0.402 seconds: 208 indexed, 193 downloads, 15 source only |
| Separate native libcurl HTTPS catalog request | 0.309899 seconds; HTTP 200; certificate verified |
| Original skin JSON | 3,029,461 bytes; 2,003 Image definitions counted recursively |

The engine probes create a separate instance and do not construct the Force UI. They do not queue installs, move plugins or change settings. Normal startup can update diagnostic files and catalog caches. The first probe was intentionally closed after the observation window; the resulting callback-aborted log entry is probe cancellation, not proof that a real user load failed.

## Interpretation

The new STORAGE work cannot be the sole cause: the old binary also exhibits the reported delay. Binary loading and direct parameter enumeration are fast in isolation. Catalog startup showed intermittent delay, but repeated successfully in under half a second. The separate successful download does not rule out intermittent DNS, connection or server delays during other requests.

Screen construction remains an unmeasured candidate: the original skin already contains roughly 2,000 image definitions and thousands of parameters. Definition count alone does not prove the UI causes the delay. No measured end-to-end Force UI load duration or before/after skin comparison has yet been captured.

## Next diagnostic steps

1. Add bounded timestamped startup-stage logging: catalog download begin/end and result, catalog parse, device probe, installed-plugin scan, data publication, first host display request. Preserve error details without per-image or per-frame logging.
2. Measure actual host screen opening alongside these stage timestamps; separate catalog readiness from first visible/usable screen.
3. If the catalog is responsible, show the cached/bundled catalog immediately and refresh in the background with a bounded timeout.
4. If screen creation dominates, compare a temporary simplified thumbnail skin while retaining parameter IDs and the matched binary/skin package. Do not attribute improvement without measuring.
5. Keep expensive drive checks deferred to STORAGE, but verify that the host does not request hidden controls at startup before relying on the pending display-request trigger.

Pending lazy-storage source changes remain uncommitted and undeployed. The temporary test manager disappeared at reboot as expected; this does not mean its source changes were lost.

## Follow-up controlled testing

- Removed 1,350 online fallback cells via a temporary bind over TUI.json. User reported no improvement (30–45 seconds). The existing application could have cached the skin, so this alone does not establish the fallback cells' cost.
- Host main-thread sampling recorded approximately 25 seconds at nearly one full core during loading. This is active CPU work rather than a sleeping network wait, but does not identify the exact host operation.
- Instrumented current source in an isolated process: download complete at 0.303 s; parse at 0.310 s; first device probe at 0.312 s; cache/source work at 0.473 s; second probe at 0.475 s; installed scan at 0.479 s; catalog published at 0.481 s. This isolated build includes the pending deferred-storage change and does not render a Force screen.
- Added opt-in worker stage timing to source. Enabled only by `/tmp/pluginmgr/startup-trace.enabled`; separate 32 KiB rotating log; no audio-thread logging. Location UI and catalog stability tests pass.
- Restarted only the application to clear skin caching. The current temporary test skin removes all 606 normal thumbnail widgets as well as the 1,350 fallback widgets, so activation can be verified visually. The old binary is unchanged. Awaiting MENU → Plugin navigation to perform this cache-cleared comparison.
- A host-call timing proxy was validated separately: original manager hash preserved; 5,571 parameters, legacy pixel parameters start at 161. Creation plus three metadata-enumeration passes took 0.030 s. Proxy is staged but not mounted over the live binary.

### Current rollback

The only live manager override is the skin file bind mount. Unmount `/usr/share/Akai/Content/Synths/poloq - VST - Plugin Manager/Plugin Skins/TUI.json` and reload the application to restore the original skin. No plugin moves, installs, or preference edits were performed in these startup tests. Temporary pointer and screenshot helpers are present; display capture now discovers the DRM display device after reboot.

## Cache-cleared UI measurement

Selected Plugin Manager remotely and recorded one screen frame approximately every second. The same original binary SHA-256 `4f7958fc50a925031f9ad3639822bfd12c4aae18b09a2b8f394b36b13fc4f314` was used. The loaded skin hash matched the no-thumbnail test file (`98b21d790c54306b66200fccc9eb94cf537f9f8fc1736e50582f46c5101a7de4`). The first completed screen visibly has no catalog thumbnails, proving that Force used the modified skin.

Last loading frame: sampled between 25.379 and 25.921 seconds after SELECT. First completed catalog frame: sampled between 26.371 and 26.920 seconds. Sampling includes SSH/frame capture overhead; this is an approximately 26-second measurement, not subsecond UI timing.

Removing all 606 standard thumbnail widgets and 1,350 online fallback widgets did not remove the slow load. The 5,400 legacy image parameters remain exposed by the binary and are a separate candidate; their contribution has not yet been measured in the real host.

## Next comparison staged: reduced parameter count

A temporary proxy delegates to the exact original manager binary but exposes 171 parameters instead of 5,571. It removes the 5,400 pixel parameters (original indices 161–5560), remaps subsequent controls and host automation callbacks, and uses a matching no-thumbnail skin. It verifies the original parameter count and pixel-block starting index before accepting an instance. This is a diagnostic experiment, not a production migration or a saved-project compatibility solution.

The isolated parameter enumeration test passed; creation plus three enumeration passes took 0.010755 s. The separate audio-processing probe passed with expected silent output. The actual Force UI load for this variant has NOT yet been measured.

The application has been restarted with temporary bind mounts for BOTH `plugin_manager.so` and `Plugin Skins/TUI.json`. A new empty test project is open. Waiting for the hardware MENU → Plugin/chooser navigation requested from the user. Source originals remain intact under both mounts. `/data/openplugin/test-backups/20261106-763ce438/rollback-startup-test.sh` stops the application, removes only these two mounts, checksums the original files, and starts the application again; it does not restore old preferences or registrations. Reboot also removes the test mounts.

## Root cause confirmed and source fix

Owner reported approximately 0.5 seconds for the reduced-parameter diagnostic build, versus approximately 26 seconds with 5,571 parameters and no image widgets. This identifies the legacy pixel-parameter block as the dominant delay. The production-source implementation removes the runtime pixel pipeline and uses ordinary bundled PNGs, a gradient fallback and bounded titles. Complete build has 228 parameters; all functional IDs match the previous STORAGE development build. Relevant native/skin/wrapper regressions pass.

## Complete static-PNG build deployed

The diagnostic proxy and its two file mounts were removed. A complete matched manager folder is now temporarily bind-mounted from `/data/openplugin/test-backups/20261106-763ce438/manager-static-png/poloq - VST - Plugin Manager`. Binary SHA-256: `ff7e0f676b21cd4fd586f1b517910cc8bd970f6258a7bcdbff10397d66c38095`. On-device probe confirms 228 parameters, 0.000591 s dlopen, 0.000272 s instance creation. All existing functional IDs match the prior STORAGE development build. The application was restarted successfully. End-to-end screen timing of this complete build still awaits user navigation; the 0.5 s report applies to the preceding diagnostic build.

Rollback for the current folder mount: `/data/openplugin/test-backups/20261106-763ce438/rollback-static-png.sh`. Reboot restores the firmware manager. No plugin moves, installs, or preference restores were performed. Missing-image downloads were requested as a follow-up and documented in CATALOG-PREVIEWS.md; this build uses bundled PNGs and gradients only.
