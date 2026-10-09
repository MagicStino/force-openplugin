# Download images

Hosted as public [GitHub Release assets](https://github.com/MagicStino/force-openplugin/releases/tag/v3.9.1.6-openplugin-research), version **3.9.1.6-openplugin**:

| Device family | Image | SHA256 |
|---|---|---|
| Akai Force | [Force IMG](https://github.com/MagicStino/force-openplugin/releases/download/v3.9.1.6-openplugin-research/Force-3.9.1.6-openplugin-UNTESTED.img) | `45420ac36669244c8b4a55dfb1acd927f0b46dd85296f5ba1be6e0798c93622d` |
| MPC Gen1 | [MPC Gen1 IMG](https://github.com/MagicStino/force-openplugin/releases/download/v3.9.1.6-openplugin-research/MPC-Gen1-3.9.1.6-openplugin-UNTESTED.img) | `59829228d311c870df8c11c30ef8d8c7d5c9cd1344f8a0297bd56d6a51b43e1f` |

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
The release also provides matching `.sha256` and `.json` validation files.
Verify the downloaded image against its checksum before copying it to USB.
Do not extract the IMG, write it as a bootable USB image, or rename it to evade
an updater check.

This project does not yet provide a hardware-validated USB flashing procedure.
Use the manufacturer’s [MPC update guide](https://support.akaipro.com/en/support/solutions/articles/69000816160-akai-pro-mpc-firmware-update-walkthrough) or [Force update guide](https://support.akaipro.com/en/support/solutions/articles/69000828125-akai-pro-force-firmware-update-walkthrough) for your exact model’s update media and recovery route; stop if the updater rejects the image. Copying a file to USB
is not evidence that it can safely be installed.

Generic release images have OpenPlugin SSH disabled. For an owner-key build,
see [SSH setup](SSH.md). The stock application remains 3.9.1.2. Build sources
and exact input hashes are in the repository; the release includes validation
manifests and [candidate results](ILLUSTRATED-CANDIDATES.json).
