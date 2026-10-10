# Catalog pictures — 0.8 RC2 correction

The native manager uses immutable per-plugin indexed pictures. Pagination and filtering select a picture by the visible plugin ID, restoring the behaviour before RC1.

RC1 replaced those frames with three writable row PNGs. The Akai host cached the original pictures, so names changed while images stayed on their original rows. RC2 removes the writable-row skin paths and disables background preview downloading. Startup and Refresh catalog still update metadata and versions, with saved-catalog offline fallback.

Pictures currently come from the hash-locked bundled snapshot. New or changed native screenshots require a manager/image build; online screenshot refresh is not supported in this release. Unknown plugins show neutral artwork instead of another plugin’s picture. The website continues to use publisher image URLs.

Regression tests cover next/previous page image mapping and filtered catalog polling; generated skin checks cover all picture options and layout. Hardware acceptance of RC2 remains pending.
