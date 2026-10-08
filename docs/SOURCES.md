# Source packages

Most users use the built-in catalog. FIND starts in search mode. Add source
accepts a GitHub owner/repo or HTTPS repository URL; Check source reads its
latest stable GitHub release. Scanner v1 considers at most 24 assets ending
in -mpc-armv7.zip. It requires GitHub HTTPS download URLs and GitHub SHA-256
asset digests. Downloads are capped at 256 MiB and verified before manifest
extraction. Scanning never runs package scripts.

Each archive must contain one package folder with mpc-plugin.json:

```json
{"schema":1,"id":"example-synth","name":"Example Synth","version":"1.0.0",
 "kind":"instrument","arch":"armv7","layout":"portable",
 "source_repo":"owner/repository"}
```

kind is instrument or effect; addins currently use the built-in catalog only.
IDs use lowercase letters, digits and hyphens. Packages must ALSO satisfy the
pinned mpc-vst-plugins portable installer convention. Manifest acceptance does
not prove executable compatibility or publisher trust. Install scripts execute
with device privileges when a user installs the package.

Imported entries persist in /data/openplugin/sources.json. The main catalog
wins duplicate IDs. Existing imported IDs are not automatically updated on
re-scan. Source removal/update tracking and publisher trust UI are future work.
Hakai-associated native packages can use this convention; firmware patches,
activation bypasses, desktop VSTs and web apps are outside the package format.
