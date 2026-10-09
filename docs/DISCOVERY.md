# Find plugins and make a project discoverable

## For musicians

Open the [catalog](https://magicstino.github.io/force-openplugin/#catalog).
All indexed entries appear without a search query. Filter by instruments,
effects, samplers, trackers or tools. Each card shows its author, description,
license, picture when available, project documentation and an action:
**View release** for a listed package, or **View source** for source-only work.
The website does not install software on your device. Read the project's
instructions and device requirements before trying a package.

On the experimental device interface, use CATALOG for the index and FIND to
filter it. FIND → Add source accepts `owner/repository` or a GitHub project URL.
The existing device source scanner checks the latest release for portable
ARMv7 packages with SHA256 digests and an `mpc-plugin.json` inside the archive.
A normal GitHub project, a Windows VST or a README alone is not installable.

## Where the data comes from

The scheduled [catalog bridge](../tools/catalog_bridge.py) starts with
https://sd88me.github.io/mpc-vst-plugins/catalog.json. It validates identities,
HTTPS release URLs and checksum fields while preserving existing package
metadata. The app reads our resulting
https://magicstino.github.io/force-openplugin/catalog.json.
The website reads the simultaneously generated `assets/catalog.json`, so its
visible cards update in the same job. `discovery.json` lists search candidates
and source notices separately from the indexed catalog.

Every six hours, GitHub Actions also searches the configured GitHub queries
and checks bounded candidate repositories for `openplugin.json` at the root
of their default branch. This is repository discovery, not a complete internet
crawl. GitHub rate limits, indexing delays and scheduled-job delays apply.
Manual **Run workflow** is available in Actions. A primary-source failure,
empty catalog or unexpected large shrink aborts publication and retains the
previous catalog. Individual discovery failures appear in the report.

## Suggest a plugin without editing JSON

Use the [Submit a community plugin form](https://github.com/MagicStino/force-openplugin/issues/new?template=plugin-submission.yml). A GitHub account is required. Supply the public project URL, name/author and what should be added or updated. You can suggest someone else’s project; authors can supply the manifest and package links.

An issue is a request, not an automatic catalog edit. A maintainer reviews it and adds the repository to `catalog/sources.json`. After that change is merged, the scheduled or manual catalog workflow fetches the root manifest and publishes both the device JSON and website cards. New entries appear as source only until package review enables downloads. On the device, **Refresh catalog** fetches the published result. **FIND → Add source** affects that device, not the shared server registry.

For an existing registered project, publish updated package metadata in `openplugin.json`; the next successful bridge refresh picks it up. For sd88me catalog entries, correct the upstream catalog instead: it takes precedence when a repository is already present there.

## For plugin authors

1. Publish a public repository with clear English documentation and a license.
2. Put `openplugin.json` at its root, using the
   [minimal example](../catalog/example.openplugin.json) and
   [schema](../schema/community-plugin.schema.json).
3. Add useful GitHub topics such as `mpc-plugin` or `akai-force`, where relevant.
   Topics improve discovery; they do not establish compatibility or approval.
4. Add a readable screenshot hosted on the permitted GitHub image hosts.
   Do not include logos/artwork you cannot redistribute.
5. Validate your manifest:

```sh
python3 tools/catalog_bridge.py --validate /path/to/openplugin.json --repo owner/repository
```

6. Submit your repository to `catalog/sources.json` through a pull request or
   [issue](https://github.com/MagicStino/force-openplugin/issues). People who do
   not know GitHub can ask the author to submit it. A registry entry is the
   dependable route; automated search is supplementary.

Use `kind` for the host class (`instrument`, `effect`, `addin`) and `category`
for the browse category (`synth`, `effect`, `sampler`, `tracker`, `tool`).
A tracker does not become a host-compatible instrument merely through labeling.
`summary`, `name`, `author`, `license`, `tags` and `images` drive the cards.
Keep descriptions factual. Omit packages when the project has source only.

## Publishing a package

The community discovery manifest is separate from the existing
`mpc-plugin.json` package manifest. It does not replace the upstream packaging
format or installer. A declared package has these fields:

```json
{
  "version": "1.0.0",
  "arch": "armv7",
  "layout": "portable",
  "devices": ["force", "mpc-gen1"],
  "url": "https://github.com/owner/repository/releases/download/v1.0.0/plugin-mpc-armv7.zip",
  "size": 123456,
  "sha256": "<64 hexadecimal characters from the actual archive>"
}
```

Put this object in `packages` only after building the archive and calculating
its real size and hash. The placeholder above intentionally fails validation.
Packages must follow the existing portable package/install contract; see
[SOURCES.md](SOURCES.md). The bridge reads metadata only: it does not execute
installers, download binaries to audit them, or prove host compatibility.

New manifest-based repositories are listed as source only until maintainers
review the package/install contract and add the repository to
`reviewed_manifest_repositories`. Existing upstream packages retain upstream
status and warnings; inclusion is not an OpenPlugin hardware test or endorsement.

## Meaning of status

- **Discovered candidate:** repository search found it; absent/unusable manifest.
- **Listed only:** valid identity/metadata; no enabled package download.
- **Metadata validated:** acceptable release URL and checksum syntax; binary
  contents and device operation are not proven by this check.
- **Hardware verified by OpenPlugin:** currently false for every entry.
  Upstream hardware reports remain attributed reports, not our validation.

## Images on the device

The website reads upstream screenshot URLs live. Native previews are a separate,
hash-locked build snapshot: 57 images for 71 IDs, with placeholders elsewhere.
Scheduled catalog updates do not silently change firmware artwork. See
[ILLUSTRATED-CARDS.md](ILLUSTRATED-CARDS.md) for reproducibility and limitations.
