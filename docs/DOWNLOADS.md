# Download images

## Current build: firmware 3.10.0 / OpenPlugin v0.8.2-rc4

The current Force and MPC Gen1 images are based on stock firmware **3.10.0** (application **3.10.0.49**). Both include OpenPlugin, SSH/SFTP support and the mouse/cursor integration.

Download the **[OpenPlugin v0.8.2-rc4 release](https://github.com/MagicStino/force-openplugin/releases/tag/v0.8.2-rc4)** below. These images include the refreshed catalog with Clif Loss and online thumbnail fallback. The larger 64 × 64 paging targets and catalog/install text from RC3 are retained.

| Device family | Current filename | SHA256 |
|---|---|---|
| Akai Force | [Force-3.10.0-openplugin-v0.8.2-rc4-update.img](https://github.com/MagicStino/force-openplugin/releases/download/v0.8.2-rc4/Force-3.10.0-openplugin-v0.8.2-rc4-update.img) | `e8d30304dce9a39249bed0faf1d3c8bb1d9d2a4f6bceb1cd6cc4276cd888fa52` |
| MPC Gen1 | [MPC-3.10.0-Gen1-openplugin-v0.8.2-rc4-update.img](https://github.com/MagicStino/force-openplugin/releases/download/v0.8.2-rc4/MPC-3.10.0-Gen1-openplugin-v0.8.2-rc4-update.img) | `f17fc3fcba9e94d96b7e531143474264107c6ca732f0ea6b52ec63c5f8fcd89f` |

## Validation status

- Both images pass container, filesystem, injected-file and stock ARM image verification.
- Offline thumbnail download/cache, corrupt-download recovery and bounded display-update tests pass.
- Full RC4 flash/boot, online thumbnail appearance and audio-load testing remain pending. MPC Gen1 is hardware untested.

## Catalog thumbnails

Connect to the internet and select **CATALOG → Refresh catalog**. Bundled thumbnails appear immediately. Entries without bundled artwork download a compact 30 × 15 thumbnail, cached for offline use. Failed downloads keep a previously valid cached image. This manager update must be installed to enable the online fallback.

## Installing from USB

1. Back up projects and connect the device to reliable power.
2. Use the image for your device family. Verify its SHA256 against the table above.
3. Copy the actual `.img` file outside any folders on a FAT32/exFAT USB drive with at least 1 GB of space. Do not extract the image or write it as a bootable USB disk.
4. Safely eject the drive, connect it to the device, then open **MENU → Preferences → Info → Update → USB Drive Update**.
5. If already running stock 3.10.0, the updater may offer a same-version update. OpenPlugin does not increase the stock application version. Keep power connected until completion and restart.
6. Open **PLUGINS → VST → Plugin Manager**, connect to the internet and select **CATALOG → Refresh catalog**.

Both filenames include the OpenPlugin version and end in `-update.img`. If an image is not detected, a copy can be renamed to `Force-3.10.0-update.img` or `MPC-3.10.0-Gen1-update.img` for the corresponding device. Renaming does not resolve an image validation error.

USB update steps follow Akai's [Force guide](https://support.akaipro.com/en/support/solutions/articles/69000828125-akai-pro-force-firmware-update-walkthrough) and [MPC guide](https://support.akaipro.com/en/support/solutions/articles/69000816160-akai-pro-mpc-firmware-update-walkthrough). These guides describe stock updates, not endorsement of this custom firmware.

## Force boot-time update mode

If the Force cannot reach its settings, Akai documents holding **MATRIX + LOAD + SAVE** while powering it on to enter Update Mode. Connect directly to a Mac or Windows computer and use the official Force updater for recovery. Do not interrupt an active firmware write.

## SSH and mouse

SSH/SFTP is enabled at startup in these builds. The default login is **username `root`, password `mpc`**. Remote-access controls are in **Plugin Manager → REMOTE ACCESS**; see [SSH.md](SSH.md). Mouse/cursor support is included; see [MOUSE.md](MOUSE.md) for setup and limitations. Inclusion does not establish that every mouse feature has been tested on 3.10.

## Older release — firmware 3.9.1

[OpenPlugin v0.8.1-rc2 release assets](https://github.com/MagicStino/force-openplugin/releases/tag/v0.8.1-rc2) remain available for reference. They are based on **3.9.1**, not the current **3.10.0** build.

RC4 adds the approved three-head Magic Tape Echo thumbnail and final catalog versions: Magic Tape Echo 0.1.1, PulyTek 1.0.2 and TinyFreaky 0.4.1. Older versions of these three are removed from the current catalog.

RC4 adds online fallback for future unbundled catalog artwork and includes the updated Clif Loss install entry.
