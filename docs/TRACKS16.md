# Tracks16 — 16 audio + 16 plugin tracks

Complete patched firmware 3.10.0 images for Akai Force and MPC Gen1. Plugin Manager 0.8.3, SSH/SFTP, mouse integration and the Open MPC catalog/artwork remain included. No manual patching is needed.

Tracks16 raises both allocation checks from 8 to 16. The overall track limit is unchanged. Only two application bytes change in each root filesystem; all other files and metadata match the previous Open MPC build.

## Validation

Both images pass filesystem, AZ01 container round-trip and stock Akai ARM verifier checks. The original and patched allocation predicates pass 1,050 emulated cases per device. SHA256SUMS and detailed validation reports are attached.

The Force image is byte-for-byte identical to the image tested by the owner: creating, saving and loading 15 audio plus 15 plugin tracks, playback, and rejection of a 17th track were reported working. Recording was not tested; saving/reloading exactly 16 of each was not explicitly reported. MPC Gen1 has passed software validation but has not been tested on hardware.

## Install

Download the image for your device family and verify SHA256SUMS. Back up projects, copy the .img to USB and install through the device firmware updater. See [the USB guide](https://github.com/MagicStino/force-openplugin/blob/main/docs/DOWNLOADS.md). Plugin Manager is available under PLUGINS → VST → Plugin Manager.

Higher track counts are not a performance guarantee. Projects exceeding stock limits may not load on unmodified firmware. Original firmware and earlier releases remain unchanged. SSH/SFTP is included; see [remote access controls](https://github.com/MagicStino/force-openplugin/blob/main/docs/SSH.md).

## Reproduce the patch

Use the exact base images from `v0.8.3-open-mpc-test.20261104`. The builder checks the full base-image hash, original application hash, both ARM instructions and the patched application hash. Unknown inputs are rejected. It modifies the existing filesystem blocks without replacing the application inode, then requires read-only filesystem checks, extraction round-trip and the stock verifier to pass before writing the final image.

```sh
python3 tools/build_tracks16.py --device force --base /path/to/Force-3.10.0-openplugin-v0.8.3-local-20261104-update.img --stock-root /path/to/force-root --qemu /path/to/qemu-arm --output /path/to/new-force-update.img
python3 tools/build_tracks16.py --device mpc-gen1 --base /path/to/MPC-3.10.0-Gen1-openplugin-v0.8.3-local-20261104-update.img --stock-root /path/to/mpc-root --qemu /path/to/qemu-arm --output /path/to/new-mpc-update.img
```

The stock roots must be extracted from the corresponding original firmware and contain its ARM libraries and az01-image verifier. Linux prerequisites include Python 3, e2fsprogs and qemu-arm. For isolated ARM tests, install Unicorn and run `tools/test_track_limits_arm.py --device force --app /path/to/original/MPC --output force-tests.json` (or `mpc-gen1`). These tests exercise allocation logic, not the complete audio engine.

Exact hashes and the full 124-byte instruction signature are in `openplugin/track_limits.py`. Patch sites are discovered uniquely inside executable ARM ELF segments; the addresses below are observations for this release, not patch inputs. Force compares are at 0x02933cb8 (plugin) and 0x02933ce0 (audio); MPC Gen1 compares are at 0x02934090 and 0x029340b8. These are immediate constants in a shared allocation predicate, not a mutable settings pointer. The Force overall limit initializes to 128; this patch does not modify overall-limit logic on either device.

The normal base build remains available; building it alone does not apply Tracks16.

## Adding future firmware safely

Unknown firmware is rejected, even if its instruction signature matches. Never copy the old addresses into a new release. Extract the new application, review its allocation predicate and callers, establish a unique executable signature and new device-specific full input/output hashes, then add a reviewed profile. Changed or duplicate signatures must fail closed. Re-run emulated boundary tests, filesystem/container/vendor verification, and device tests before publishing. The relocation tests ensure the matcher follows moved code and rejects ambiguous, altered or non-executable matches. Stock images must remain untouched and each build requires a new output path.
