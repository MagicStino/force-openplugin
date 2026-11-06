# MagicStino OpenPlugin 0.9.0

A major manager update for Akai Force: quicker browsing, clearer controls and managed plugin storage beyond Internal.

## Highlights

- Fast bundled PNG artwork replaces thousands of image parameters; readable descriptions and centered, subdued navigation buttons.
- A–Z, Z–A, Newest, Oldest and Popular sorting. Letter groups jump immediately and refine to individual letters, with the correct paginator page.
- Move eligible manager-installed plugins from Internal to SSD/USB/SD and back. Verified cleanup frees source space; new compatible installs follow the selected manager location.
- Drive/free-space overview, missing-drive guidance, move preparation/copy/verification progress and concise support logs.
- Automatic skin-registration maintenance after successful installs plus a manual Repair plugin skins action.
- Persistent SSH controls with visible IP, port and login hint.
- ABOUT tab: MagicStino OpenPlugin, version 0.9.0, one GitHub repository link for the manual and source.
- Existing Tracks16 support retained: 16 audio + 16 plugin tracks, with original overall limits unchanged.

## Release scope

The new image targets **Force 3.10.0**. This release does not produce a new MPC Gen1 image. Keep the previously published MPC Gen1 download and its hardware-test limits separate.

Owner testing confirmed the manager's fast startup, date sorting, restored skin/header and Internal ↔ SSD moves. Screenshots are genuine Force captures. The 0.9.0 image has now flashed and booted successfully on the owner’s Force; SSH reports version 0.9.0 and the real ABOUT screen confirms the manager and skin. Storage across reboot, audio and track-limit checks on this exact image remain pending. See the accompanying validation report and [manual](GUIDE.md).

Missing artwork remains a gradient until a later package supplies artwork. Missing skin files require reinstalling the affected plugin. Only manager-owned, eligible packages are moved; unsupported symbolic links and hard-coded content paths are not promised portable.

## Upgrade

The Force image includes the manager, permanent volume startup hook, registration, remote-access controls and Tracks16. Flash only the correct Force image via the normal firmware updater after verifying its checksum. A standalone manager package is also built for controlled upgrades; it is not a replacement for installing all firmware services on an unmodified system.

## Community credits

**NoQuestion & dustyslices**: first documented the VST method in the MPC-Forums thread [“Proof of Concept: Custom Standalone Plugins”](https://www.mpc-forums.com/viewtopic.php?f=41&t=220981) (September 2026), as credited by [Open MPC](https://github.com/open-mpc/mpc-vst-plugins#credits).

Thanks to [poloq](https://github.com/poloq-instruments/mpc-vst-manager) for the original Plugin Manager, [sd88me / Open MPC](https://github.com/open-mpc/mpc-vst-plugins) for the catalog setup, collection and tooling, and [MockbaTheBorg / MockbaMod](https://github.com/MockbaTheBorg/MockbaMod) for SSH, screen and mouse information and community code. Mouse-code credits to no3z, Amit Talwar and bonsaipanda are preserved alongside the original licenses.
