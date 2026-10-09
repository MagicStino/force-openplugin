# Refreshing available plugins

On Force/MPC, open Plugin Manager → CATALOG and tap **Refresh catalog** at the bottom. It downloads the server JSON, updates cards and compares available versions with installed versions. It does not install anything automatically. Use FIND → Show all if a filter hides entries.

A successful refresh says **Catalog refreshed from server**. A failed refresh keeps the current index, or loads the saved catalog after restarting, and shows an offline/failure message. Reconnect and tap Refresh catalog to retry. The saved file is `.pluginmgr-catalog.json` beside the manager's settings base. Corrupt, empty, duplicate-ID and oversized catalogs are rejected.

The [GitHub workflow](https://github.com/MagicStino/force-openplugin/actions/workflows/catalog.yml) runs every six hours, scans configured community sources and discovery queries, writes `website/catalog.json` plus card metadata, and deploys Pages. Maintainers can use **Run workflow** to refresh earlier. The device fetches that published result; it does not run a GitHub scan itself.

New repositories without reviewed compatible packages remain source-only. Versions follow published community metadata; an arbitrary new GitHub release is not automatically a compatible installer. Failed primary-source refreshes and unexpected index shrinkage abort publication, preserving the previous server catalog.

Two-year maintenance goal: pinned builds, checked downloads, offline fallback and failure tests reduce breakage. They cannot guarantee upstream availability or untested hardware compatibility. Keep a known-working IMG, checksum and stock recovery image; review Action failures and test each update on hardware before recommending it widely.
