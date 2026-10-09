# OpenPlugin Research

An experimental community instrument and plugin browser for **Akai Force and
MPC Gen1**, developed with AI. Independent, non-commercial and unaffiliated
with Akai or inMusic.

**Start here: [Download and update in four steps](https://magicstino.github.io/force-openplugin/#downloads).**

The HTML site is published at https://magicstino.github.io/force-openplugin/; its source is `website/index.html`.
After the initial USB update, open **PLUGINS → VST → Plugin Manager** and install compatible plugins from the touchscreen.

[Browse plugins](https://magicstino.github.io/force-openplugin/#catalog) ·
[USB download instructions](docs/DOWNLOADS.md) · [Find or publish a plugin](docs/DISCOVERY.md) ·
[Package format](docs/SOURCES.md) · [Validation](docs/TESTING.md)

**Hardware status:** the owner reports successful Force use and ROM download.
MPC Gen1 and the new combined setup remain unverified on hardware. Research candidates.

![Generated native catalog preview — not a hardware capture](website/assets/catalog-native.png)

## What it does

- Browse community instruments, effects, samplers, trackers and tools.
- Show plugin previews, descriptions, authors, licenses and package versions.
- Filter the catalog or add a compatible GitHub release through FIND.
- Queue installation, updates and removal in the native manager.
- Refresh the online catalog and website cards on a six-hour schedule.
- Tap **Refresh catalog** on the device to fetch available plugins and versions; it does not install updates.
- JV setup offers **Install ROMs + plugin**. Save first: completion restarts the app.

For existing 3.9.1 users: the updater can ask to reinstall the **same version, 3.9.1**.
The OpenPlugin build number labels our additions; the stock internal version remains unchanged.
See [catalog refresh](docs/CATALOG-REFRESH.md).

The current index has 71 entries and 57 bundled native previews. Unknown images
use placeholders. New source packages require review; inclusion is not a
hardware compatibility guarantee. See [image sources and limits](docs/ILLUSTRATED-CARDS.md).

## Build both images

Linux prerequisites: Python 3.12+, git, gcc, e2fsprogs, binutils, OpenSSH tools,
Chromium runtime libraries, several GB of RAM and approximately 5 GB of space.
Use the exact original files recorded in `inputs.json`.

```sh
git clone https://github.com/MagicStino/force-openplugin.git
cd force-openplugin
bash build.sh /path/Force-3.9.1-update.img \
  /path/MPC-3.9.1-Gen1-update.img /path/output
```

Outputs: `*-openplugin-v0.7-update.img`, checksums and validation manifests. Existing files
are not overwritten. The script fetches pinned dependencies and builds the
native code, artwork and both images without mounting them. It does not flash.
OpenPlugin 0.7 adds automatic device-password SSH/SFTP and a REMOTE ACCESS tab. See [Remote Access](docs/SSH.md); physical login and SFTP still need testing.

Development container version: **3.9.1-openplugin-v0.7**. The supplied 3.9.1 files
contain application **3.9.1.2**; its binaries and numeric version fields stay
unchanged. [Current OpenPlugin 0.7 research release](https://github.com/MagicStino/force-openplugin/releases/tag/v0.7-openplugin-research-rc2). IMG files are release assets, not Git files.

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

Credits: [poloq Plugin Manager](https://github.com/poloq-instruments/mpc-vst-manager)
and [MPC VST Plugins](https://github.com/sd88me/mpc-vst-plugins).
Existing component licenses apply; see [NOTICE](native/NOTICE.md).

## Real Force photos

[View the owner-supplied hardware gallery](https://magicstino.github.io/force-openplugin/#force-gallery): catalog, combined JV-880 setup, plugin selection and plugin interfaces. MPC imagery is labelled as a rendered preview.

## Community credits

**sd88me**: [MPC VST Plugins](https://github.com/sd88me/mpc-vst-plugins), the upstream catalog JSON and collection, and the native wrapper/skin/build tooling used here. Individual plugin authors and their upstream engines, ports, screenshots and artwork retain their credits and licenses.

**poloq-instruments**: [Plugin Manager](https://github.com/poloq-instruments/mpc-vst-manager), the native manager foundation, including existing device-side installation. Our additions integrate it into the firmware, add illustrated cards/search improvements, a scheduled catalog bridge, saved-catalog fallback and combined JV setup.

## Community catalog contributions

[Suggest a plugin](https://github.com/MagicStino/force-openplugin/issues/new?template=plugin-submission.yml), support an existing proposal with 👍, or [volunteer as a maintainer](https://github.com/MagicStino/force-openplugin/issues/new?template=maintainer-application.yml). [Community review guide](docs/COMMUNITY-CATALOG.md) explains the maintainer acceptance action, review pull requests and GitHub notifications. Submissions never enable installers automatically.
