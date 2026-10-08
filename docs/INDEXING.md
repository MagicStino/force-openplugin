# Catalog and connectivity

The current index contains 71 entries: 31 instruments, 37 effects and 3 tools;
69 have a listed package. Samplers overlap instruments. All entries are
browsable without a query; source-only entries cannot be installed.

Try `acid`, `reverb`, `Airwindows` or `Lucky Dip` in FIND. **Show all** clears
the filter. FIND searches loaded metadata, not the whole internet.

The online [bridge](DISCOVERY.md) runs every six hours and updates both the
app catalog and website cards. Repository search results remain review
candidates until they have usable metadata. Installation is never automatic.

On the device, **Refresh** requests the online catalog. Imported sources persist
in `/data/openplugin/sources.json`; the main catalog currently has no persistent
offline cache or automatic refresh on reconnection. A failed refresh retains
the current in-memory view. Source addition checks the latest stable release
using the [package contract](SOURCES.md).
