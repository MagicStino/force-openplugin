# Local Open MPC migration candidates — 4 November 2026

These local candidates use stock firmware 3.10.0 (application 3.10.0.49).
They are new bytes, distinct from the published v0.8.3 images. Filenames carry
`local-20261104`; the internal OpenPlugin/container version remains 0.8.3.
Do not replace the published release with these files without hardware acceptance.

The source combines main d2091a9 with the build/runtime changes from the
checksum-verified OpenPlugin-0.8.3-source.zip (SHA256
baec061466227c92ed7215f5e2ca36e269847830cc773ab4378d48dc613c44f7).
Current main catalog/workflow fixes were preserved.

## Open MPC migration

The catalog bridge reads https://open-mpc.github.io/catalog.json. The native
manager reads the merged OpenPlugin catalog so reviewed local additions remain
available, saves the last successful catalog and has a bundled offline snapshot.
The tooling repository is https://github.com/open-mpc/mpc-vst-plugins; its pinned
commit is unchanged. Plugin IDs, author credits, individual repositories,
installer paths and immutable download hashes are preserved. In particular,
JV-880's installed folder still uses its original sd88me name.

The refreshed snapshot has 200 entries with matching website/native/artwork IDs,
195 locked screenshots and five explicit fallback images. After Gen1 filtering,
188 entries offer downloads. No IDs were removed. Download versions for six Gen2-only entries are intentionally
withheld on this Gen1 build; native parsing applies the same architecture guard
even when reading the currently published online catalog. ARMv7 downloads with
"gen2-test" in the release tag remain available. MPC Sample remains an excluded review candidate: its
manifest returns 404, also present in the prior published snapshot. Discovery
search requiring a GitHub token was not run locally. Scheduled Actions supplies
its own token. A thumbnail re-render from the lock matched the first rendering.

## Build corrections

The Python environment now propagates to executable upstream render helpers.
After replacing upstream preview controls with the native bitmap layout, the
builder removes only unreferenced top-level sh_mode PNG files. This removes 606
unused files (9.55 MB), preserves all 478 referenced PNGs and fits the original
rootfs without resizing or removing any stock file. Tests now exercise unbundled
online previews separately from native bundled artwork and use isolated caches.
The wrapper regression checks the documented 12-callback bound and eventual
readiness for online fallback, rather than the obsolete zero-callback behavior.

## Reproduce

Use build.sh with the exact inputs pinned in inputs.json for a complete source
build. The accompanying source archive also includes release-payload, the exact
locally built payload, for tools/build.py. Always choose a new output directory.
The scripts preserve original inputs and refuse to overwrite an existing image.
The local image-validation helper compares every stock regular file and symlink,
allows only the intended /etc/shadow update, and runs the original ARM verifier,
plugin loader and native tests under QEMU. It expects .deps/test-load-arm and
.deps/test-native-arm built from tests/test_load.c and tests/test_native.c.

Full flash/boot, touchscreen artwork, installation, project recall and audio-load
acceptance on hardware remain pending for these exact bytes. A checksum and
successful software verification do not establish those hardware results.
