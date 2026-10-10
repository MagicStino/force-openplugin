# Download images

Hosted as public [GitHub Release assets](https://github.com/MagicStino/force-openplugin/releases/tag/v0.8-openplugin-research-rc2), version **OpenPlugin 0.8 RC2 on firmware 3.9.1**:

| Device family | Image | SHA256 |
|---|---|---|
| Akai Force | [Force IMG](https://github.com/MagicStino/force-openplugin/releases/download/v0.8-openplugin-research-rc2/Force-3.9.1-openplugin-v0.8-rc2-update.img) | `210989e221fa49d746210d5823822b1977ac6d674d151c32645e607f05d77d5b` |
| MPC Gen1 | [MPC Gen1 IMG](https://github.com/MagicStino/force-openplugin/releases/download/v0.8-openplugin-research-rc2/MPC-3.9.1-Gen1-openplugin-v0.8-rc2-update.img) | `111b09f1a30024531615cd2805a0393ec228664a92515020411ca7021dc4cbfe` |

**Test candidate:** both images pass stock image verification and filesystem checks. These 0.8 images have not been flashed or boot-tested. Earlier Force use does not establish new mouse, image-refresh or search-CPU behaviour. MPC Gen1 remains hardware unverified. Use only your device family’s image and stop if the updater rejects it.

## Existing 3.9.1 users

The updater may ask whether to update the **same version, 3.9.1**. This is expected:
the internal stock application version remains 3.9.1.2; our development build number
is not presented as a higher stock firmware version. Confirm the same-version update
to install the OpenPlugin additions, after backing up projects and choosing the correct device image.

## Downloading for USB

Download the actual `.img` through the link above, not GitHub’s source-code ZIP.
Download the matching `.sha256` release asset and verify the IMG before renaming or copying. `.json` files record structural validation. Do not extract the IMG or write it as a bootable USB image.

The filenames are `Force-3.9.1-openplugin-v0.8-rc2-update.img` and `MPC-3.9.1-Gen1-openplugin-v0.8-rc2-update.img`. If not detected, rename to `Force-3.9.1-update.img` or `MPC-3.9.1-Gen1-update.img` respectively. Renaming helps discovery; it does not bypass compatibility checks.

For an existing 3.9.1 installation:

1. Back up projects and connect the device to reliable power.
2. Copy the correct IMG outside any folders on a FAT32/exFAT USB drive (1 GB or larger). Safely eject it, then plug it into the device.
3. Open **MENU → Preferences → Info → Update → USB Drive Update**.
4. Confirm the same-version update if prompted; keep power on until completion and restart.
5. Open **PLUGINS → VST → Plugin Manager** on a plugin track. Connect to the internet and tap **CATALOG → Refresh catalog**.

USB menu/media steps follow Akai’s [Force guide](https://support.akaipro.com/en/support/solutions/articles/69000828125-akai-pro-force-firmware-update-walkthrough) and [MPC guide](https://support.akaipro.com/en/support/solutions/articles/69000816160-akai-pro-mpc-firmware-update-walkthrough). These guides describe stock updates, not approval of this custom image. Stop if the updater rejects it. Owner-reported Force success does not validate every model; MPC Gen1 remains hardware unverified.

SSH/SFTP controls are available in **Plugin Manager → REMOTE ACCESS**. See the [connection guide](SSH.md); earlier Force login and file transfers passed, while MPC Gen1 remains unverified. Mouse setup and limits are in [MOUSE.md](MOUSE.md). The stock application remains 3.9.1.2.
