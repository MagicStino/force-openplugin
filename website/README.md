# OpenPlugin Research website

Static English guide with beginner/developer routes, original SVG artwork, generated native FIND previews, source/package/extension how-tos, AI attribution, research mission and a 71-entry catalog snapshot. No analytics, accounts, third-party fonts or website plugin installation. Plugin cards link to their upstream repositories and load available upstream screenshots over HTTPS without copying them into this repository. Image requests reach the upstream hosting provider; images may be absent or change. Catalog content is displayed as text, not executable HTML.

Preview from the repository root:

```sh
python3 -m http.server 8765 --directory website
```

Open http://127.0.0.1:8765. JavaScript uses a local catalog.json; serve over HTTP rather than opening the HTML as a local file.

## Free GitHub Pages

The current private repository cannot use free public Pages. Making it public exposes repository contents/history and releases and requires the owner's explicit approval. Alternative: publish only this website directory in a separate public repository. Do not copy firmware, keys, personalized images or local outputs into that repository.

Once that decision is approved, copy the contents of website/ to the publishing branch root and select that branch / (root) in Settings > Pages. Keep .nojekyll. The site uses relative asset links and works at a project Pages URL. No paid hosting account is required. This source preparation does not itself enable Pages.

Update the catalog snapshot and validation claims deliberately when upstream or binaries change. Illustrations are concepts; native previews are generated assets and not real-device screenshots.
