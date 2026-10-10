# Illustrated device interface

The native CATALOG page now has three illustrated cards per screen: plugin
title, two short description lines, author, declared license, version and
existing installation controls. CPU and legacy warnings appear in the metadata
line where applicable. Descriptions are author metadata, not compatibility
guarantees. Empty descriptions get an explicit fallback.

The 2026-10-08 snapshot contains 71 IDs and 57 upstream previews. Fourteen
entries without a usable image use a neutral placeholder. Unknown IDs use the
same placeholder; empty rows use a transparent image. The website catalog
and native manager remain separate interfaces.

## Reproducible artwork

`assets/previews.lock.json` records source URLs, hashes and author repositories.
`tools/build_previews.py` downloads only approved HTTPS image hosts, limits
size and image dimensions, verifies SHA256, then produces 176 × 86 PNGs.
The regular native build invokes this tool; changed upstream bytes cause a
build failure rather than silently changing the result. Cached original bytes
live in `.deps/previews/`. A clean build needs internet for these locked inputs.
Earlier indexed-frame builds required `native/preview_index.h` to match the lock. OpenPlugin 0.8 uses writable row images instead.

Maintainers can deliberately review a new snapshot with:

```sh
python3 tools/build_previews.py --update-lock --output build/previews
```

Review the lock, attribution, fallback reasons and generated ID header before
committing them. Package license fields do not independently grant image rights.
The payload ships the source/credit lock and NOTICE.

## Original bundled-only implementation (historical)

Images are bundled, so displaying an existing preview needs no device network
request. The host skin format uses indexed images; it does not load arbitrary
image URLs. New sources retain their title, description, author, license and
repository in the imported-source cache, but need a reviewed build to gain a
thumbnail. This does not add background discovery or an offline main catalog.

## Historical validation

The illustrated ARM plugin builds and loads under QEMU against both supplied
Force and MPC Gen1 root filesystems. Offline native tests cover description
wrapping, unknown-ID fallback, all 71 image mappings and source metadata cache
round trips; six Python container/build tests also pass. Generated layouts and
images can be checked without hardware. These checks do not prove host skin
rendering, memory use, touchscreen behavior, installation or flash acceptance
on a physical device. The published 3.9.1.3 release predates illustrated cards.

## OpenPlugin 0.8

Bundled images are now fallback artwork for the background per-plugin cache. The skin points to writable row PNGs; see [CATALOG-PREVIEWS.md](CATALOG-PREVIEWS.md) for refresh logic and unresolved host-cache validation. The old indexed-frame description above applies to earlier releases only.
