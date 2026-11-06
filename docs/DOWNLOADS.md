# Download images

## OpenPlugin 0.9.0 — new Force candidate

The new Force-only candidate is `Force-3.10.0-openplugin-v0.9.0-update.img`. It includes Manager 0.9.0, managed SSD/removable storage, skin repair, About/manual links, SSH/SFTP and Tracks16. The new image has flashed and booted on the owner’s Force, with Manager 0.9.0 and its ABOUT skin confirmed. Storage across reboot, audio and track-limit acceptance on this exact image remain pending.

[0.9.0 release notes](RELEASE-0.9.0.md) · [User manual](GUIDE.md). The previously published images below remain available while the candidate is validated. No new MPC Gen1 image was built for this release.

## Current build: Tracks16 / firmware 3.10.0 / OpenPlugin v0.8.3 — 5 November 2026

**16 audio + 16 plugin tracks**, with the overall limit unchanged. These are complete patched images; no manual patching is needed. See [Tracks16 details](TRACKS16.md).

The current Force and MPC Gen1 images are based on stock firmware **3.10.0** (application **3.10.0.49**). Both include OpenPlugin, SSH/SFTP support and the mouse/cursor integration.

Download the **[current Open MPC release](https://github.com/MagicStino/force-openplugin/releases/tag/v0.8.3-tracks16.20261105)** below. These exact images include the Open MPC migration, a bundled snapshot of 200 plugins and 195 artwork images, and Gen1 download filtering. The larger 64 × 64 paging targets and readable catalog text are retained.

| Device family | Current filename | SHA256 |
|---|---|---|
| Akai Force | [Force-3.10.0-openplugin-v0.8.3-tracks16-update.img](https://github.com/MagicStino/force-openplugin/releases/download/v0.8.3-tracks16.20261105/Force-3.10.0-openplugin-v0.8.3-tracks16-update.img) | `21cfb6150ca77ae5cb79c7acf89ebd0a2c9faf4502c69957594e994977fac2df` |
| MPC Gen1 | [MPC-3.10.0-Gen1-openplugin-v0.8.3-tracks16-update.img](https://github.com/MagicStino/force-openplugin/releases/download/v0.8.3-tracks16.20261105/MPC-3.10.0-Gen1-openplugin-v0.8.3-tracks16-update.img) | `3ca8d26b2e2288a134bbf11c092b46eb2563b7cae2627859bfd2bcf680e433f5` |

## Validation status

- Both images pass container, filesystem, injected-file and stock ARM image verification.
- Offline thumbnail download/cache, corrupt-download recovery and bounded display-update tests pass.
- Force owner testing confirms creation, saving and loading of 15 audio plus 15 plugin tracks, playback and rejection of a 17th track. Recording remains untested. MPC Gen1 passes software validation but remains hardware untested.

## Included artwork and catalog

Clif Tape, TinyFreaky, PulyTek and Magic Tape Echo have bundled artwork. The plugin binaries are not embedded or automatically installed; select Install in the manager to download their ready-built packages.

## Catalog thumbnails

Connect to the internet and select **CATALOG → Refresh catalog** for newer plugin releases. The image bundles 195 artwork images; five entries use fallback artwork. Online thumbnail cache and bounded update tests pass. The owner reports the Force build works; this does not establish every remote artwork case.

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

The previous Open MPC release and its original filenames remain available unchanged. Tracks16 is the current download.

## Older release — firmware 3.9.1

[OpenPlugin v0.8.1-rc2 release assets](https://github.com/MagicStino/force-openplugin/releases/tag/v0.8.1-rc2) remain available for reference. They are based on **3.9.1**, not the current **3.10.0** build.

0.8.2 adds the approved three-head Magic Tape Echo thumbnail and final catalog versions: Magic Tape Echo 0.1.1, PulyTek 1.0.2 and TinyFreaky 0.4.1. This historical snapshot is superseded by subsequent online catalog updates.

0.8.3 corrects the missing Clif Tape image registration and updates artwork generation to use the merged catalog.

## Older manager-only update

The following standalone ZIP predates the 4 November Open MPC firmware build and does not contain all of its migration changes. Use the current firmware image above for the tested build.

Existing OpenPlugin 0.8.x users can download the [ready-built Plugin Manager 0.8.3](https://github.com/MagicStino/force-openplugin/releases/download/v0.8.3/Plugin-Manager-0.8.3-mpc-armv7.zip). No compiling or firmware flash is needed. Follow the included INSTALL.md and choose a writable, executable Synths location. Save first: installation restarts the music application. The package includes an uninstaller.
