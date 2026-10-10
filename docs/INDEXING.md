# Catalog and connectivity

Browse all indexed community plugins without a query, or try `acid`, `reverb`, `Airwindows` or `Lucky Dip` in FIND. **Show all** clears the filter. FIND searches loaded metadata, not the whole internet. Source-only entries cannot be installed.

The server [bridge](DISCOVERY.md) runs every six hours and publishes the device index and website cards. Registered compatible packages need review before downloads are enabled. Entry counts change; see the [published index](https://magicstino.github.io/force-openplugin/catalog.json).

The manager loads that index when opened and when **Refresh catalog** is pressed. Successful loads save `.pluginmgr-catalog.json` beside the settings base. If a request fails, the manager keeps its existing index or reads the saved copy. Reconnect and refresh to retry; there is no continuous polling or reconnection trigger.

Imported sources persist in `/data/openplugin/sources.json`. Add source checks the latest stable release against the [package contract](SOURCES.md). Package updates require an explicit install action.

OpenPlugin 0.8 RC2 restores bundled indexed pictures; automatic online image refresh is disabled. See [preview behaviour and hardware limits](CATALOG-PREVIEWS.md).
