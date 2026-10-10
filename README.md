# OpenPlugin

Browse, install and update **community VST plugins on Akai Force 3.9.1 and MPC Gen1**, directly from the touchscreen. OpenPlugin also brings combined JV-880 ROM/plugin setup, community USB mouse support and SSH/SFTP file transfers.

Built on [poloq’s Plugin Manager](https://github.com/poloq-instruments/mpc-vst-manager) and [sd88me’s MPC VST Plugins](https://github.com/sd88me/mpc-vst-plugins). Original authors retain their credits and licenses. This independent, non-commercial project is AI-assisted and unaffiliated with Akai or inMusic.

**[Download OpenPlugin 0.8 RC1 and follow the USB guide](docs/DOWNLOADS.md).** After the initial update, load **PLUGINS → VST → Plugin Manager** on a plugin track.

[Browse plugins](https://magicstino.github.io/force-openplugin/#catalog) · [Find or publish a plugin](docs/DISCOVERY.md) · [Test status](docs/TESTING.md)

**Release status:** 0.8 RC1 is a research candidate. Both images pass structural and stock verifier checks; the new images have not been flashed or boot-tested. Earlier Force use and SSH/SFTP transfers are documented. Mouse interaction, refreshed touchscreen images and the search CPU fix still need device acceptance testing; MPC Gen1 remains unverified on hardware.

![Generated native interface preview — not a hardware capture](website/assets/catalog-native.png)

## What it does

- Discover community instruments, effects, samplers, trackers and tools; filter by name, author or tag.
- Download compatible native packages, queue installs and updates, or remove managed plugins.
- Load the online index when the manager opens or **Refresh catalog** is pressed; keep a saved index offline.
- Fetch and cache plugin pictures in the background, with bundled fallback artwork. Host image reloads still need hardware confirmation.
- Prepare **JV-880 ROMs + plugin** in one action. Save first: installation restarts the application.
- Add a community USB mouse pointer with click/drag and wheel support, subject to the display compatibility guard.
- Transfer samples and files using **REMOTE ACCESS** SSH/SFTP controls. See the [connection guide](docs/SSH.md) for setup and test limits.

Only compatible ARMv7 community packages can be installed. General web pages, desktop VST bundles and source repositories alone are not installable packages. Refreshing the index does not install software automatically.

For existing 3.9.1 users, a same-version update prompt is expected: the original application remains **3.9.1.2**. See the [USB guide](docs/DOWNLOADS.md).

## Build from original firmware

Linux prerequisites: Python 3.12+, git, gcc, e2fsprogs, binutils, OpenSSH tools,
Chromium runtime libraries, several GB of RAM and approximately 5 GB of space.
The owner already supplied both original stock **3.9.1** firmware images for
this project: `Force-3.9.1-update.img` and `MPC-3.9.1-Gen1-update.img`.
Their exact SHA256 checksums are recorded in [inputs.json](inputs.json).
They are not stored in Git; use those supplied local files, or matching original
copies. Other firmware versions are rejected; renaming them does not help.

Clone the repository and place your original images in a `firmware/` folder
inside it (or substitute their actual paths below):

```sh
git clone https://github.com/MagicStino/force-openplugin.git
cd force-openplugin
mkdir -p firmware
```

Build **Force only**; no MPC image is required:

```sh
bash build.sh --device force firmware/Force-3.9.1-update.img output-force
```

Build **MPC Gen1 only**; no Force image is required:

```sh
bash build.sh --device mpc-gen1 firmware/MPC-3.9.1-Gen1-update.img output-mpc
```

Or build **both**:

```sh
bash build.sh firmware/Force-3.9.1-update.img \
  firmware/MPC-3.9.1-Gen1-update.img output
```

Each command builds the native payload and runs the same validation checks;
only the requested firmware image(s) are generated. The originals remain unchanged.
An optional final argument supplies an owner's public SSH key.

Outputs: `*-openplugin-v0.8-update.img`, checksums and validation manifests. Existing files
are not overwritten. The script fetches pinned dependencies and builds the
native code, artwork and selected images without mounting them. It does not flash.

Development container version: **3.9.1-openplugin-v0.8**. The supplied 3.9.1 files
contain application **3.9.1.2**; its binaries and numeric version fields stay
unchanged. [Current OpenPlugin 0.8 research release](https://github.com/MagicStino/force-openplugin/releases/tag/v0.8-openplugin-research-rc1). IMG files are release assets, not Git files.

## Documentation

| Need | Read |
|---|---|
| Find plugins or list your project | [Discovery](docs/DISCOVERY.md) |
| Package a native plugin | [Package contract](docs/SOURCES.md) |
| Understand catalog/network behavior | [Indexing](docs/INDEXING.md) |
| Inspect image and firmware changes | [Integration](docs/INTEGRATION.md) |
| Check what was actually tested | [Validation](docs/TESTING.md) |
| Understand purpose and rights | [Research](docs/RESEARCH.md) |

Package installers run with device privileges and are not transactional.
Desktop VSTs, arbitrary websites and sample editors are not native packages.
Hakai compatibility must be assessed per package. MPC Sample is a separate
kit editor; kit import is not implemented here.

Existing component licenses apply; see [NOTICE](native/NOTICE.md).

## Real Force photos

[View the owner-supplied hardware gallery](https://magicstino.github.io/force-openplugin/#force-gallery): catalog, combined JV-880 setup, plugin selection and plugin interfaces. MPC imagery is labelled as a rendered preview.

## Community credits

Mouse source: [no3z, Amit Talwar and bonsaipanda](https://github.com/bonsaipanda/MPC-Force-SSH-Firmwares). Image decoding: [stb](https://github.com/nothings/stb). Pinned sources and licenses are preserved in `native/`.

**sd88me**: [MPC VST Plugins](https://github.com/sd88me/mpc-vst-plugins), the upstream catalog JSON and collection, and the native wrapper/skin/build tooling used here. Individual plugin authors and their upstream engines, ports, screenshots and artwork retain their credits and licenses.

**poloq-instruments**: [Plugin Manager](https://github.com/poloq-instruments/mpc-vst-manager), the native manager foundation, including existing device-side installation. Our additions integrate it into the firmware, add illustrated cards/search improvements, a scheduled catalog bridge, saved-catalog fallback and combined JV setup.

## Community catalog contributions

[Suggest a plugin](https://github.com/MagicStino/force-openplugin/issues/new?template=plugin-submission.yml), support an existing proposal with 👍, or [volunteer as a maintainer](https://github.com/MagicStino/force-openplugin/issues/new?template=maintainer-application.yml). [Community review guide](docs/COMMUNITY-CATALOG.md) explains the maintainer acceptance action, review pull requests and GitHub notifications. Submissions never enable installers automatically.

## Repository maintenance

For catalog refreshes, use the [update-plugins skill/runbook](.agents/skills/update-plugins/SKILL.md): commands, validation and removal review, commit/push, and GitHub Pages verification.
