# Download images

Hosted as public [GitHub Release assets](https://github.com/MagicStino/force-openplugin/releases/tag/v3.9.1.7-openplugin-research-rc2), version **3.9.1.7-openplugin**:

| Device family | Image | SHA256 |
|---|---|---|
| Akai Force | [Force IMG](https://github.com/MagicStino/force-openplugin/releases/download/v3.9.1.7-openplugin-research-rc2/Force-3.9.1-update.img) | `654a34ede3c2a8a343c90d3cf87e8d3e4cd5ca3bedccbb7dc713b27f9bb2dfd9` |
| MPC Gen1 | [MPC Gen1 IMG](https://github.com/MagicStino/force-openplugin/releases/download/v3.9.1.7-openplugin-research-rc2/MPC-3.9.1-Gen1-update.img) | `66589fbbc358ab855f4f4f292df89b07e2f97f51237e738e7827f51627088233` |

**Research status:** the owner reports successful Force use, including plugins and ROM download.
This is not comprehensive hardware validation. The MPC Gen1 candidate is the relevant family
for an original MPC One, but no physical MPC One has been tested. Preserved
board IDs alone do not establish model compatibility. Never use the Force
image on an MPC or bypass updater checks.

## Existing 3.9.1 users

The updater may ask whether to update the **same version, 3.9.1**. This is expected:
the internal stock application version remains 3.9.1.2; our development build number
is not presented as a higher stock firmware version. Confirm the same-version update
to install the OpenPlugin additions, after backing up projects and choosing the correct device image.

## Downloading for USB

Download the actual `.img` through the link above, not GitHub’s source-code ZIP.
Use [SHA256SUMS-USB.txt](https://github.com/MagicStino/force-openplugin/releases/download/v3.9.1.7-openplugin-research-rc2/SHA256SUMS-USB.txt) for the USB filenames. Developer `.sha256` files retain the original build filenames; `.json` files record validation.
Verify the downloaded image against its checksum before copying it to USB.
Do not extract the IMG or write it as a bootable USB image.
The latest downloads already use the stock filenames: `Force-3.9.1-update.img`
and `MPC-3.9.1-Gen1-update.img`. If using an older development-named IMG,
rename it to the appropriate stock filename. Renaming helps file discovery;
it does not bypass firmware compatibility checks.

For an existing 3.9.1 installation:

1. Back up projects and connect the device to reliable power.
2. Copy the correct IMG outside any folders on a FAT32/exFAT USB drive (1 GB or larger). Safely eject it, then plug it into the device.
3. Open **MENU → Preferences → Info → Update → USB Drive Update**.
4. Confirm the same-version update if prompted; keep power on until completion and restart.
5. Open **PLUGINS → VST → Plugin Manager** on a plugin track. Connect to the internet and tap **CATALOG → Refresh catalog**.

USB menu/media steps follow Akai’s [Force guide](https://support.akaipro.com/en/support/solutions/articles/69000828125-akai-pro-force-firmware-update-walkthrough) and [MPC guide](https://support.akaipro.com/en/support/solutions/articles/69000816160-akai-pro-mpc-firmware-update-walkthrough). These guides describe stock updates, not approval of this custom image. Stop if the updater rejects it. Owner-reported Force success does not validate every model; MPC Gen1 remains hardware unverified.

Generic release images have OpenPlugin SSH disabled. For an owner-key build,
see [SSH setup](SSH.md). The stock application remains 3.9.1.2. Build sources
and exact input hashes are in the repository; the release includes validation
manifests and [candidate results](ILLUSTRATED-CANDIDATES.json).
