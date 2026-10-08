# JV-880 content setup

The JV SETUP touchscreen tab is implemented in source, but is **not included in the published 3.9.1.4 firmware**. Hardware testing is pending. Missing ROMs and the generic red-bar parameter interface are separate issues; this setup does not claim to fix the skin.

The [plugin author](https://github.com/sd88me/mpc-vst-jv880/blob/master/docs/ROMS.md) requires your own JV-880 v1.0.0 dump and warns that v1.0.1 causes emulator CPU traps. ROMs are not in the plugin package or our firmware.

## Touchscreen flow

Install JV-880, save your project and unload all its instances before importing. Open **JV SETUP**:

- **Check files** lists each required filename and checks its size at the registered plugin location. This does not identify the firmware revision or prove that audio works.
- **Download** shows the third-party archive notice; tap it again to confirm. The app fetches the external [community archive](https://archive.org/details/jv880_rompack_v1), verifies its pinned SHA-256, and extracts only the five required files. The download needs internet and 200 MiB temporary free space. The source is not endorsed by the plugin author. Use files you are entitled to use.
- **Import USB** finds `jv880_rompack_v1.zip` at a mounted USB/SD drive root under `/media` or `/mnt`. It accepts the same pinned archive. Arbitrary personal dumps are currently copied manually following the author's instructions; there is no general file picker yet.

Existing files are never overwritten, including user NVRAM. A wrong-size existing file is reported and must be moved aside manually before retrying. Successful setup asks you to close and reload JV-880; it does not restart the device automatically.

## Exact inventory

| Required file | Bytes |
|---|---:|
| `jv880_rom1.bin` | 32768 |
| `jv880_rom2.bin` | 262144 |
| `jv880_waverom1.bin` | 2097152 |
| `jv880_waverom2.bin` | 2097152 |
| `jv880_nvram.bin` | 32768 |

Destination: `<installed JV-880 folder>/jv880-roms/roms/`.

The archive additionally contains 19 optional SR-JV80 expansions (01–19), which belong in `roms/expansions/`. This first setup flow imports only the base five files; expansions remain manual. `rd500_expansion.bin` and `rd500_patches.bin` are unrelated and excluded.

Inspected archive SHA-256: `f29a3d59bce0e46696d6b618fe8c2d40d2db92459a8e7c2ca114f196cfde7cf4`. All 26 members passed ZIP CRC checks and the five base files match the required sizes. This fingerprint establishes identity with the inspected archive, **not independent verification of v1.0.0 or permission to redistribute**.

## Validation

Offline C tests cover size/type checks, copying missing files, preserving existing user state and refusing unrelated plugin registrations. Native manager regression tests pass with ASan/UBSan (leak detection disabled because the execution environment uses tracing). Touchscreen and download/import on real Force/MPC hardware remain untested.
