# Catalog preview refresh (0.8 candidate)

The manager downloads its catalog when opened and when Refresh catalog is pressed. Preview downloads run on its background worker, never in audio rendering or host parameter reads. Browsing another page requests previews for the three visible cards. There is no periodic network polling.

HTTPS screenshots are decoded, scaled to the generated card dimensions, and saved under `/data/openplugin/previews`. Each catalog ID has a persistent cache. Startup and explicit refresh fetch screenshots again, including URLs whose content changed without a version change. Offline operation falls back to saved images, then bundled images, then generic artwork. Only changed row pixels request a display update. A generation check prevents an outdated page request replacing the current page.

Downloads have connection and total time limits and bounded input sizes. Decoder dimensions are limited. PNG, JPEG, GIF and BMP are supported. Image encoding and decoding occur outside the mutex used by host parameter polling. Upstream stb source and licenses are shipped with the source and payload notices.

## Validation and remaining hardware test

Offline codec/cache tests exercise malformed input, path rejection, PNG round trips, offline fallback and unchanged-image display stability. The generated skin uses absolute writable row image paths. A simulated layout render checks dimensions and labels; it does **not** prove the Akai host reloads changed images rather than its filmstrip cache. That behaviour must be confirmed on hardware before claiming preview refresh works for every user. Mouse interaction and the filtered CPU fix also require device acceptance testing. Do not describe this candidate as hardware verified.
