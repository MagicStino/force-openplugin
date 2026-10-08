# OpenPlugin for Force and MPC Gen1

Experimental native touchscreen community plugin browser, built into user-supplied
Akai firmware. Project/container version: **3.9.1.3-openplugin**. Both supplied
images contain application **3.9.1.2**, despite their 3.9.1 filenames. Application
binaries and numeric version fields remain unchanged.

**Development candidates only: flashing, boot, touchscreen operation, audio and
plugin installation/removal on hardware are NOT TESTED. Checksums and successful
builds do not establish that flashing is safe.**

## Features

- Native discovery/installed/update cards, filters, storage/progress indicators,
  queued installation/update/removal and restart confirmation, derived from
  poloq's MIT-licensed Plugin Manager.
- New FIND page: touchscreen keyboard and search by name, maker or tag. Most
  users never need to know GitHub. Add source is a separate optional mode.
- GitHub latest-release scanner for compatible portable ARM packages with
  SHA-256 verification and manifest validation. Imported entries persist on
  internal storage. Scanning never executes package scripts.
- Expanded 512-entry catalog; HTTPS-only, bounded downloads and fail-fast apply.
- Optional owner-key-only SSH with unique per-device host keys. No Telnet,
  shared password or embedded private key.
- Unmounted deterministic AZ01/rootfs build adapter for both exact stock inputs.

Installing a package runs its own scripts with device privileges. A checksum
verifies downloaded bytes, not publisher trust. CPU/audio/ABI compatibility
requires per-plugin hardware testing. Installation is not transactional.

## Build both candidates

Requires Linux, Python 3.12+, git, gcc, e2fsprogs (debugfs/e2fsck), binutils,
OpenSSH client tools and Chromium runtime libraries. Allow several GB RAM and
roughly 5 GB working space. No root, mounts or device connection required.

```sh
git clone https://github.com/MagicStino/force-openplugin.git
cd force-openplugin
ssh-keygen -t ed25519 -f "$HOME/.ssh/openplugin_ed25519"
bash build.sh /path/Force-3.9.1-update.img /path/MPC-3.9.1-Gen1-update.img \
  /path/output "$HOME/.ssh/openplugin_ed25519.pub"
```

The fourth argument is optional: omit it to disable OpenPlugin SSH. Supply only
a PUBLIC key and keep the private key on your computer. The script fetches
pinned dependencies, builds ARM code and artwork, runs tests and builds both
images. Dependency checkouts are read from committed Git trees, ignoring edits.
Input SHA-256 values in inputs.json are enforced. Different firmware needs
new inspection and adapter validation.

Outputs: `*-UNTESTED.img`, `.sha256` and `.json` validation manifests. Existing
outputs are never overwritten. Repeat into different empty directories and
compare SHA-256 values; public keys and all other inputs must be identical.

```sh
python3 -m unittest discover -s tests -v
gcc -O1 -fsanitize=address,undefined -fno-omit-frame-pointer \
  tests/test_native.c -lpthread -ldl -lm -o /tmp/openplugin-test
ASAN_OPTIONS=detect_leaks=0 /tmp/openplugin-test
```

## SSH

After updater/recovery validation and eventual installation, connect locally:

```sh
ssh -i "$HOME/.ssh/openplugin_ed25519" root@DEVICE_IP
```

A separate service uses /data/openplugin/ssh for unique host keys; stock vendor
keys/config remain intact. Password/interactive authentication and forwarding
are disabled. Root's password field changes from an account lock to `*`, an
unusable password, to allow public-key login. No password is enabled. Actual
network login still requires a device test. Never publish an owner's private
key or distribute personalized SSH firmware as a generic image.

Registration requires an existing Settings/*/MPC.settings profile. Factory-reset
first boot, boot ordering and upgrades have not been validated on hardware.
See [integration](docs/INTEGRATION.md) and [source format](docs/SOURCES.md).

## Community content

Built-in collection: https://sd88me.github.io/mpc-vst-plugins/ . Hakai-associated
native plugins are eligible when supplied in compatible MPC packages; there is
no claim that all Hakai plugins load. Firmware scripts and desktop VSTs are not
automatically compatible. Exact packages still require hardware testing.

https://github.com/WorldLinkStudio/mpcsample is a browser/desktop kit editor,
not a native plugin. Its .xpj export is a possible future kit-import workflow;
it is not ported/bundled here. Sample preview/download/import is not implemented.
Imported-source updates/removal and a publisher trust UI remain future work.

## Distribution

IMG files exceed GitHub's 100 MiB per-file limit and are excluded from Git.
This source build uses owner-supplied stock firmware, without redistributing it.
No firmware release has been published. If redistribution rights and hardware
validation are established, publish generic builds WITHOUT an owner's SSH key
as prerelease assets, together with hashes/manifests and exact source commit:

```sh
gh release create 3.9.1.3-openplugin --prerelease \
  --title 'OpenPlugin development' --notes-file release-notes.md \
  /path/output/*.img /path/output/*.sha256 /path/output/*.json
```

## Credits

Engine/base skin: https://github.com/poloq-instruments/mpc-vst-manager (MIT).
Wrapper/tooling/catalog: https://github.com/sd88me/mpc-vst-plugins (MIT, with
component licenses). Pins: dependencies.json; credits: native/NOTICE.md and
native/LICENSE. Not affiliated with Akai or inMusic.
