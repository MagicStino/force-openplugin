# OpenPlugin Research website

Static English guide with beginner/developer routes, original SVG artwork, generated native FIND previews, source/package/extension how-tos, AI attribution, research mission and a 71-entry catalog snapshot. No analytics, accounts, third-party fonts or website plugin installation. Plugin cards link to their upstream repositories and load available upstream screenshots over HTTPS without copying them into this repository. Image requests reach the upstream hosting provider; images may be absent or change. Catalog content is displayed as text, not executable HTML.

Preview from the repository root:

```sh
python3 -m http.server 8765 --directory website
```

Open http://127.0.0.1:8765. JavaScript uses a local catalog.json; serve over HTTP rather than opening the HTML as a local file.

## Free GitHub Pages

The owner approved making the repository public. The documentation site is published from the gh-pages branch root at https://MagicStino.github.io/force-openplugin/. Source lives in website/ on main. To update the deployment, copy the contents of website/ to the gh-pages root, preserving .nojekyll and relative asset paths. Never copy firmware, keys or local output directories into the website branch.

Update the catalog snapshot and validation claims deliberately when upstream or binaries change. Illustrations are concepts; native previews are generated assets and not real-device screenshots.

## Pending with the next firmware image build

Update and publish the guide alongside the next image release, per the user's 6 November 2026 request. Use the preserved screenshots in `assets/screenshots/2026-11-06/` and the release checklist in `../docs/LOCATIONS-UPGRADE.md`. Cover the catalog/install queue, STORAGE moves and cleanup, skin repair and persistent Remote Access. Validate the permanent external-storage startup hook with a real reboot before replacing the temporary-test limitation. Screenshot assets are saved; guide content and publication remain pending.
