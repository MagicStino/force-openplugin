# Catalog images: website and native manager

Website cards load each catalog entry's HTTPS screenshot dynamically. PulyTek's public preview is present in the catalog and returns a valid PNG.

The native manager uses a built-in hash-locked filmstrip (`assets/previews.lock.json` and `native/preview_index.h`). Refresh catalog fetches JSON metadata only; it cannot add image frames to the installed Akai skin or add mappings to its compiled manager. An unknown plugin ID uses the NO PREVIEW frame even when the catalog includes a screenshot URL.

PulyTek is appended to the preview lock and index, preserving every existing frame number. `tools/build_native.py` builds the updated manager binary and Akai skin with the new frame; both must be distributed together. The current installed manager still needs that update to show the picture. A new firmware image is not intrinsically required: a validated manager-only update can replace the manager binary and skin together. Do not copy just the PNG or just the index, as that does not update the installed mapping/filmstrip.

For future submissions, review and hash-lock the screenshot and append its ID to the bundle as part of manager packaging. Metadata acceptance alone provides the website picture and device download listing, but cannot promise a thumbnail on an older manager. Automatic remote thumbnail loading is not currently implemented.
