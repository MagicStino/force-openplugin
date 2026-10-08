# Download images

Hosted as public [GitHub Release assets](https://github.com/MagicStino/force-openplugin/releases/tag/v3.9.1.4-openplugin-research), version **3.9.1.4-openplugin**:

| Device family | Image | SHA256 |
|---|---|---|
| Akai Force | [Force IMG](https://github.com/MagicStino/force-openplugin/releases/download/v3.9.1.4-openplugin-research/Force-3.9.1.4-openplugin-UNTESTED.img) | `44aeba2a6267825c6be031c988b8c73db05d5eac65e3875f88d30a09e6eba947` |
| MPC Gen1 | [MPC Gen1 IMG](https://github.com/MagicStino/force-openplugin/releases/download/v3.9.1.4-openplugin-research/MPC-Gen1-3.9.1.4-openplugin-UNTESTED.img) | `d871195eb112847bc2688619dc1e342e1230c3d6a2d24959a4d40083f28f58ba` |

**Hardware untested:** updater acceptance, flash, boot, touch, audio and plugin
installation are not validated. The MPC Gen1 candidate is the relevant family
for an original MPC One, but no physical MPC One has been tested. Preserved
board IDs alone do not establish model compatibility. Never use the Force
image on an MPC or bypass updater checks.

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
