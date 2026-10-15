# Live catalog images — 0.8.1 RC1 candidate

The native catalog now downloads the visible plugins' HTTPS screenshot URLs. It shows a saved thumbnail first, then a bundled fallback, and keeps the last good image when a request or decode fails. Each visible image is attempted once per catalog refresh, including unchanged URLs. Paging cancels obsolete work; a result for a previous page cannot be displayed under a different plugin.

Akai caches skin PNG files. This build therefore renders the thumbnail through stock native Image/FilmStrip components: a shared immutable RGB444 palette and a 60×30 grid of 3-pixel cells per card. Numeric parameter updates change the displayed pixels without replacing a cached image. No firmware executable patch or graphics interception is used. This intentionally reduces thumbnail detail and introduces 5,400 display-only pixel parameters. On-device screen loading and redraw performance need acceptance testing before this becomes the default release.

Network transfer and image decoding run on the worker, never inside the parameter getter. Downloads are HTTPS-only, bounded to 4 MiB during receipt, and time-limited. PNG, JPEG, GIF and BMP are decoded; unsupported or corrupt artwork uses the last good image or bundled placeholder. No software can retrieve an absent/unreachable image; a fallback is always available in the payload.

The 2026-10-15 bundled snapshot has 123 entries and 121 available publisher images. New IDs do not need a firmware rebuild to receive online images. The website continues to use the publisher's original image URL.

Validation: deterministic online-response, changed pixels, new IDs, corrupt-download, page-identity, persistence, offline and transfer-limit regressions; native skin palette/handle/bounds checks; ARM manager builds. Both candidate IMGs pass container, injected-file, filesystem and stock ARM image-verifier checks. Flash, boot, physical Force/MPC touchscreen behaviour and audio-load impact have NOT been tested. These are test candidates, not a claim of hardware acceptance.
