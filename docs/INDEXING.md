# Community index and discovery

The current saved catalog contains 71 entries: 31 instruments, 37 effects and 3 addins/tools; 69 currently have a usable HTTPS/SHA-256 package. Every entry is browsable without a query. Source-only cards remain visible but cannot be installed. Queries match name, author, id, kind and all saved tags.

Categories are All, Instruments, Effects, Trackers, Samplers and Tools. Sampler and tracker styles/tags are cross-cutting filters, not disjoint totals. The current snapshot includes Lucky Dip and Omni Sampler as samplers and no tracker. Do not claim universal Hakai compatibility: evaluate each native ARM package individually.

Try FIND: `acid`, `reverb`, `Airwindows`, `Lucky Dip`. Clear the query with Show all. FIND filters loaded entries; it does not search the whole web. The website includes a browsable snapshot, not a remote installer.

## Current networking

Refresh explicitly fetches the main catalog; offline behavior and caching differ by source. Imported compatible source entries are persisted locally and merged on successful refresh. A failed main refresh reports unavailable connectivity and leaves the current in-memory view. Automatic startup reload of a saved main catalog is not provided. Source addition scans a repository's latest stable GitHub Release only, using the format described in SOURCES.md.

## Planned, not implemented

Background discovery of new repositories, connectivity-triggered reload, refresh scheduling and persistent main-catalog offline browsing. Proposed approach: reviewed seed sources and bounded topic searches; network requests only while connected, cached catalog immediately available, one debounced refresh on reconnection, backoff/rate-limit handling and no automatic installation. New repositories should be candidates for review, not automatically trusted software sources.
