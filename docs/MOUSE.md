# USB mouse support

OpenPlugin 0.8 includes a reproducibly compiled DRM cursor preload from
[no3z / Amit Talwar / bonsaipanda](https://github.com/bonsaipanda/MPC-Force-SSH-Firmwares/tree/64b1b3785270f923549712597d793cfda606463c/ssh/mouse/src/drm_390).
Its pinned source, cursor data, attribution and Unlicense are in native/mouse.

Plug a USB mouse into the Force or MPC Gen1. The driver detects relative-motion
input devices and supports hot-plug, left-button touch/drag and wheel events.
The touchscreen stays available. Speed is configured in /etc/force_cursor.conf.
Logging is disabled by default. It initializes only inside the MPC application,
so inherited preloads do not create input threads in package installers or SSH tools.

The cursor implementation targets an 800 x 1280 physical display and checks its
DRM CRTC, idle cursor plane and property names before modifying an atomic commit.
Other display layouts pass through unchanged. This is a compatibility guard,
not proof that every MPC model has been physically tested.

The read-only compatibility probe passed on the owner's Force on 10 October
2026. No mouse was attached at inspection time; physical mouse movement,
click/drag, wheel, hot-plug and MPC Gen1 behavior remain unverified.

The systemd drop-in is /etc/systemd/system/acvs.service.d/20-openplugin-mouse.conf.
To disable mouse initialization, add an administrator override containing
Environment=OPENPLUGIN_MOUSE_DISABLED=1 and restart the application after saving.
Existing stock MPC binaries, boot firmware and application versions are preserved.
