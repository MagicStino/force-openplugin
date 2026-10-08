# Integration and validation

The exact inputs in inputs.json contain AZ01 v1 containers with one XZ rootfs
partition and SHA-1 integrity records. The parser verifies checksums, bounds
and exact EOF and rejects unknown trailing/signature records rather than
silently discarding them. The stock ARM az01-image verifier accepted both
original inputs under QEMU and reported no signing keys for their containers.
That does not establish stock updater/bootloader acceptance of custom firmware.

No executable, kernel, bootloader, signing tool, signature check, LoadPin setting
or licensed instrument activation is patched. The AZ01 string version becomes
3.9.1.3-openplugin; board/device lists and application binaries remain intact.
The rootfs adapter injects the native manager, skin, helpers and services via
debugfs without mounting. It fixes times/owners/modes, verifies all injected
files/links, checks the filesystem read-only and recompresses with XZ CRC32,
preset 1. Supplied input files remain unchanged.

Upstream already implements catalog/cards/install/update/remove. Local changes
add FIND search, keyboard/source scanning, persistence, bounded HTTPS downloads,
a larger catalog and fail-fast detached systemd application scripts. The cgroup
write fallback is removed; systemd-run is required. Artwork IDs use content
hashes instead of build paths. Upstream licenses and the font OFL ship in images.

The registration service runs before acvs, refuses to edit while MPC runs,
and calls the pinned sync tool which backs up and validates settings. It
requires an existing user profile. SSH is a separate owner-key service; the
root shadow field changes to an unusable password to permit key authentication.
Per-device host keys are generated on first service start; no shared host key
or private owner key is shipped.

Required hardware checks, NOT completed:

1. Exact MPC model and verified recovery/update procedure for each device.
2. Updater policy/signing acceptance without bypassing security controls.
3. Boot, registration, all profiles, first boot, storage/network and SSH login.
4. Touch targets, tab navigation and Q-Links on both hardware displays.
5. Trusted plugin install, launch, project save/reload, audio/CPU, update,
   uninstall and reboot.
6. Offline mode, failed downloads, full storage and interrupted install recovery.

Offline tests, emulator execution and rendered previews do not substitute for
these checks. No safe-flashing claim is made.
