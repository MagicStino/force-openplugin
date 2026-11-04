# Firmware integration

OpenPlugin 0.8.3 targets the exact stock 3.10.0 inputs recorded in `inputs.json`. The AZ01 parser checks partition bounds, SHA-1 integrity records and exact end-of-file, rejecting unknown trailers rather than discarding them. The container label becomes `3.10.0-openplugin-v0.8.3`; stock application version **3.10.0.49**, board lists, application binaries, kernel and bootloader remain intact. Activation and signature checks are not patched.

The builder injects the native manager, skin, helpers, services and notices through debugfs without mounting the filesystem. It sets deterministic metadata, verifies injected files and symlinks, checks the filesystem read-only, and recompresses it. Input images are preserved. A successful build does not prove flashing or boot safety.

The manager extends [poloq’s native Plugin Manager](https://github.com/poloq-instruments/mpc-vst-manager) using [sd88me’s wrapper and tooling](https://github.com/open-mpc/mpc-vst-plugins). Additions include FIND search, saved catalogs, source scanning, combined JV setup and the background preview cache. Installation uses detached systemd jobs; systemd-run is required. Component licenses and font notices ship in the payload.

The registration service runs before the application, requires an existing user profile, refuses to edit while MPC runs, and invokes the pinned settings-backup/validation tool. Remote access uses device-generated SSH host keys; the default build offers the REMOTE ACCESS controls, while an optional owner public-key build has a separate SSH service. No private owner key or shared host key is shipped. See [SSH.md](SSH.md).

Community mouse support is compiled from pinned source and loaded only inside the MPC application. It checks the DRM display layout before enabling pointer/input handling; unsupported layouts pass through. See [MOUSE.md](MOUSE.md).

## Validation limits

Both current images pass structural, filesystem and stock ARM verifier checks. The manager loads against both stock runtimes under emulation. On 4 November 2026, the owner tested this exact Force image and reported that everything works. This is an owner-reported hardware acceptance, not a test of every plugin or peripheral. MPC Gen1 passes software validation but remains hardware untested. See [TESTING.md](TESTING.md) for revision-specific evidence.
