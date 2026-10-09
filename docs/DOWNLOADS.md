# Download images

Hosted as public [GitHub Release assets](https://github.com/MagicStino/force-openplugin/releases/tag/v0.7-openplugin-research-rc2), version **OpenPlugin 0.7 on firmware 3.9.1**:

| Device family | Image | SHA256 |
|---|---|---|
| Akai Force | [Force IMG](https://github.com/MagicStino/force-openplugin/releases/download/v0.7-openplugin-research-rc2/Force-3.9.1-openplugin-v0.7-update.img) | `6b16b0d9834631d61d9449d46173a2051c8c639b1df03dc9176f537a12cb4b08` |
| MPC Gen1 | [MPC Gen1 IMG](https://github.com/MagicStino/force-openplugin/releases/download/v0.7-openplugin-research-rc2/MPC-3.9.1-Gen1-openplugin-v0.7-update.img) | `6b1763bf0b5bdec6ebcb22c677a86409d2d64085c11a3aef05ea4e09a7bac2f2` |

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
Download the matching `.sha256` release asset and verify the IMG before renaming or copying. `.json` files record structural validation. Do not extract the IMG or write it as a bootable USB image.

The filenames are `Force-3.9.1-openplugin-v0.7-update.img` and `MPC-3.9.1-Gen1-openplugin-v0.7-update.img`. If not detected, rename to `Force-3.9.1-update.img` or `MPC-3.9.1-Gen1-update.img` respectively. Renaming helps discovery; it does not bypass compatibility checks.

For an existing 3.9.1 installation:

1. Back up projects and connect the device to reliable power.
2. Copy the correct IMG outside any folders on a FAT32/exFAT USB drive (1 GB or larger). Safely eject it, then plug it into the device.
3. Open **MENU → Preferences → Info → Update → USB Drive Update**.
4. Confirm the same-version update if prompted; keep power on until completion and restart.
5. Open **PLUGINS → VST → Plugin Manager** on a plugin track. Connect to the internet and tap **CATALOG → Refresh catalog**.

USB menu/media steps follow Akai’s [Force guide](https://support.akaipro.com/en/support/solutions/articles/69000828125-akai-pro-force-firmware-update-walkthrough) and [MPC guide](https://support.akaipro.com/en/support/solutions/articles/69000816160-akai-pro-mpc-firmware-update-walkthrough). These guides describe stock updates, not approval of this custom image. Stop if the updater rejects it. Owner-reported Force success does not validate every model; MPC Gen1 remains hardware unverified.

OpenPlugin 0.7 starts SSH/SFTP automatically with a device-generated password. Open **Plugin Manager → REMOTE ACCESS** to see the IP, reveal the password, or disable access persistently. Username: `root`; port: 22. SFTP provides full device access, including sample folders under `/media`. See [Remote Access](SSH.md). Live SSH/SFTP and the new tab remain hardware unverified. Stock application version remains 3.9.1.2.
