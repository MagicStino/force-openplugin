# Download images

## Current build: firmware 3.10.0 / OpenPlugin v0.8.2-rc1

The current Force and MPC Gen1 images are based on stock firmware **3.10.0** (application **3.10.0.49**). Both include OpenPlugin, SSH/SFTP support and the mouse/cursor integration.

**Download availability:** these 3.10 images have been built and supplied locally, but their public GitHub Release assets have not yet been uploaded. The older release linked below is firmware 3.9.1; it is not the 3.10 download.

| Device family | Current filename | SHA256 |
|---|---|---|
| Akai Force | `Force-3.10.0-openplugin-v0.8.2-rc1-update.img` | `146df8b004fd87a433d94d9ce96e7dde86da45ca0872b775fdf9b03de637dc1a` |
| MPC Gen1 | `MPC-3.10.0-Gen1-openplugin-v0.8.2-rc1-update.img` | `bad4915ecaea5f8f60c1c13c759ced2618d079b61230a8a72ce1824589381d27` |

## Validation status

- Both images passed stock image verification, filesystem checks and injected-file verification.
- On 23 October 2026, the Force owner reported the device working after the update. A subsequent SSH login succeeded and the Force application service was active. This confirms remote access and a running application on that device; it is not a full feature or audio test.
- Mouse operation and paging CPU usage have not yet been measured on the updated Force.
- MPC Gen1 remains hardware untested.

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
