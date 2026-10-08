The manager engine in manager.c derives from poloq-instruments/mpc-vst-manager
commit 20850977d9d6b4916bc6574291790415f45254c7, under the MIT license in LICENSE.
The skin and artwork are built from that same pinned repository, with an
OpenPlugin wordmark and a decorative update badge replacing a redundant touch
button. The VST wrapper and build tools come from sd88me/mpc-vst-plugins commit
95cc428cd7d4042230cc854a780fb0b7dfa1921f, MIT (vendored components retain their
own licenses). Both licenses and the artwork font's OFL are shipped in the
payload. The original authors' hardware reports are their reports, not tests
of these modified images. See docs/INTEGRATION.md for the local changes.

Local interface additions include the FIND page, QWERTY keyboard, search and
optional GitHub source scanning/persistence. The build normalizes preset times
and uses content-based artwork IDs. See docs/TESTING.md for actual test limits.

Illustrated catalog cards use upstream plugin screenshots. The shipped
previews.lock.json records each plugin ID, author repository, declared package
license, screenshot URL and SHA256 (or a documented fallback). Screenshot
rights remain with their respective authors; package license metadata is not
a separate grant of rights for artwork. Report attribution/rights concerns
through https://github.com/MagicStino/force-openplugin/issues.
