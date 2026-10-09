# Validation scope

## Force SSH and SFTP hardware test — 10 October 2026

OpenPlugin 0.7 RC3: password login as root/mpc succeeded on the owner's Force. SFTP uploaded a 64-byte temporary file into `/tmp`, downloaded it with identical bytes and SHA256, and removed it; absence was confirmed. Mounted storage directories were listed without changing sample libraries. See [Remote Access test details](SSH.md).

This validates login and a small transfer on this Force. It does not validate writes to every sample drive, disabling/re-enabling, persistence across reboots, larger transfers or physical MPC Gen1 operation.

## Historical baseline checks

The historical image hashes and repeat-build/ARM-runtime results below refer to the earlier personalized baseline recorded in VALIDATION.json. The later catalog/category/site revision has separate candidates and must not be confused with those hashes. For that historical revision: six Python tests, native host logic tests, the real 71-entry index test and generated FIND layout checks passed; website sampler/reverb filters were checked in the browser. Hardware was untested at that stage; current Force SSH/SFTP results are above.

# Test results — 2026-10-08

Passed on the development host:

- Six Python tests: AZ01 roundtrip, deterministic packing, board/version fields,
  corrupted/truncated/unknown-trailer rejection, input preservation and fail-closed build.
- Native C tests with AddressSanitizer + UndefinedBehaviorSanitizer (leak sanitizer
  disabled in the sandbox): 100-entry catalog, checksum/size checks, audio silence,
  search/filter, key presses/releases, busy-state input protection, URL validation,
  release asset selection, source cache roundtrip/escaping and duplicate suppression.
- The same native tests compiled to ARM hard-float and run using QEMU with BOTH
  extracted stock firmware runtimes.
- Actual ARM plugin dlopen with RTLD_NOW and VSTPluginMain export lookup using
  both stock runtimes. This does not instantiate the real MPC host or test audio.
- Current community catalog downloaded over HTTPS: 71 packages parsed, 69
  downloadable entries have HTTPS URLs and 64-digit SHA-256 digests. No plugin
  installer was executed. This is a host-side network/parser test, not device Wi-Fi.
- Generated FIND UI: both modes, all 46 active touch targets within 1280x628,
  minimum 44 px, no target overlaps, all images present and sample text fits.
  Simulated previews were rendered from the actual generated TUI/PNG assets and
  visually inspected. No real touchscreen screenshot or usability study.
- Stock ARM sshd configuration evaluated with a test host key: public-key-only,
  password/interactive login disabled. Actual SSH login and first-boot host-key
  generation remain untested on hardware.
- Both final AZ01 images accepted by their ORIGINAL ARM az01-image verifier:
  verify success, correct version, partition bounds and SHA-1. No signing keys
  reported. This does not prove updater/bootloader acceptance.
- Read-only e2fsck and every injected file/symlink checked in each build.
- Both images built twice from identical stock input/native payload and compared:
  byte-identical SHA-256. Native payload builds in separate paths also matched
  after eliminating the preset wall-clock timestamp. Final skin coordinates
  changed subsequently; final image repeat tests use the final QWERTY payload.
- Stock application, az01 verifier, sshd and all boot files unchanged: seven
  Force files and nineteen MPC files. Hashes in CRITICAL-FILES.json.
- Shell syntax checks passed for build and SSH preparation scripts.

Image hashes, sizes and hardware status: VALIDATION.json. Personalized images
contain an owner's PUBLIC SSH key. Neither that private key nor stock/modified
firmware binaries are committed to this source repository.

NOT TESTED: hardware flashing/boot, updater signing policy, registration/startup
ordering, native touchscreen event routing/Q-Links, real plugin install/update/
uninstall, audio/CPU/project recall, SSH authentication, recovery/factory reset,
interrupted installs, sample kit import and arbitrary Hakai plugins.

To repeat the UI check after a build:

```sh
.deps/venv/bin/python tools/verify_skin.py build/native build/preview
```

For optional ARM checks, compile tests/test_native.c and tests/test_load.c with
Zig target arm-linux-gnueabihf.2.31, then use qemu-arm -L EXTRACTED_STOCK_ROOT.
Pass the built plugin_manager.so path to test_load. Never execute package
install scripts on the development host as a substitute for device validation.

## Scheduled catalog and illustrated cards

See [DISCOVERY.md](DISCOVERY.md) and [ILLUSTRATED-CARDS.md](ILLUSTRATED-CARDS.md).
Twelve Python tests passed (six firmware/container tests and six bridge tests).
The generated CATALOG preview checks actual image mappings, frame counts,
geometry and sample text; it is a simulated rendering, not a device capture.

## 3.9.1.7 source checks

Combined JV setup stages/checks ROMs before the plugin download and one button dispatches the combined job. The interface warns that completion restarts the app. Existing files and NVRAM are preserved; invalid existing ROM files stop preparation. An integration test executes the generated ROM-copy fragment against temporary fixtures, checks five installed file sizes and preserved NVRAM, and checks staging cleanup. No ROM content or network download is used by this test.

Thirteen Python tests, native search/ROM dispatch tests, catalog persistence and malformed/empty/duplicate-ID checks passed. The ARM plugin loads with both supplied runtime trees under emulation. Generated CATALOG/FIND bounds and text checks passed. Combined setup, persistent-cache behavior after device reboot, and physical MPC operation still require hardware validation.

Website device visuals are styled renders of generated native assets. They are not hardware screenshots. Regenerate with `tools/verify_catalog_skin.py --jv` and `tools/render_share.py` using the native build and the bundled renderer dependencies.
