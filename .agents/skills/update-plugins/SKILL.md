---
name: update-plugins
description: Refresh and review the OpenPlugin community plugin catalog, commit its generated data, and verify GitHub Pages publication.
---

# Update OpenPlugin plugins

Run from the repository root. This refreshes metadata, not installed device plugins or firmware. Sources and discovery queries live in `catalog/sources.json`; implementation and publication are defined by `tools/catalog_bridge.py` and `.github/workflows/catalog.yml`.

## Prerequisites

- Use an up-to-date, clean checkout of `main`; inspect `git status --short` and `git pull --ff-only` first. Keep unrelated work out of the update.
- Python 3 with its standard library; no extra Python packages are required for the bridge.
- Network access to `sd88me.github.io`, `api.github.com`, and `raw.githubusercontent.com`.
- Set `GITHUB_TOKEN` securely in the environment for GitHub repository discovery and authenticated API limits. Without it, search is skipped; upstream and configured repositories are still fetched. Never print or commit the token. Git push needs separately configured repository write credentials.
- Coordinate with the scheduled workflow (every six hours) to avoid racing its commits.

## Refresh and validate

Run the existing offline bridge/security tests before the refresh:

```sh
python3 -m unittest discover -s tests -p test_catalog_bridge.py
```

The exact live update command is:

```sh
python3 tools/catalog_bridge.py
```

It writes all three generated files:

- `website/catalog.json`: native/server catalog.
- `website/assets/catalog.json`: website card metadata, including download availability.
- `website/discovery.json`: discovery candidates and source errors/notices.

Run the same tests afterward, then inspect:

```sh
python3 -m json.tool website/catalog.json > /dev/null
python3 -m json.tool website/assets/catalog.json > /dev/null
python3 -m json.tool website/discovery.json > /dev/null
git diff --check
git diff --stat
git diff -- website/catalog.json website/assets/catalog.json website/discovery.json
```

Compare plugin IDs and counts against the pre-update commit, including removed versions/downloads even when total counts increase. Confirm matching IDs, version metadata and generation timestamps in both catalogs; card `download` flags must agree with available validated versions. Confirm discovery `indexed` equals the catalog count and review every `errors` entry and new candidate. Preview with `python3 -m http.server 8765 --directory website`; check the home/catalog cards, images and download/source links in a browser.

**Stop for review on any unexpected catalog shrink, plugin removal, lost download/version, source failure, malformed output or failed test. Do not commit or publish the suspect output.** The bridge only automatically rejects shrinkage below 75% of the previous count; smaller losses still require review. Inspect the cause and preserve the last good published data. Do not rerun repeatedly to conceal a failure.

**Validation and security checks must never be weakened to make an update pass.** Preserve schema/identity/duplicate/capacity checks, HTTPS host allowlists, redirect and response-size limits, package ownership/SHA256/target validation, shrink protection and all tests. Never delete the previous catalog to bypass the shrink guard. Do not add a repository to `reviewed_manifest_repositories` merely to enable a download: use the separate [community review process](../../../docs/COMMUNITY-CATALOG.md) and review the package/install contract. Metadata validation does not establish binary safety or hardware compatibility; the bridge never executes packages.

## Commit, push and verify Pages

After the review passes, stage only the three generated files:

```sh
git add website/catalog.json website/assets/catalog.json website/discovery.json
git diff --cached --check
git diff --cached
git commit -m "Refresh validated community catalog and documentation cards"
git push origin HEAD:main
```

Use the repository's review/PR route if direct push is restricted. If the push is rejected because the scheduled workflow advanced `main`, fetch and reconcile its changes, then repeat the data review; never force-push. Record the commit SHA and refresh counts/notices.

A push changing `website/**` triggers [Update community catalog and documentation cards](https://github.com/MagicStino/force-openplugin/actions/workflows/catalog.yml). It runs the tests, refreshes again with the Actions token, may create a bot data commit, uploads `website/`, and deploys Pages. Review that run's logs and any bot diff using the same removal/security criteria. Do not dispatch an additional refresh unless needed; documentation-only pushes do not match this workflow's path filter.

Wait for both `update` and `deploy` jobs to succeed and confirm the deployment corresponds to the intended commit (or its reviewed bot refresh). Verify [GitHub Pages](https://magicstino.github.io/force-openplugin/), `/catalog.json`, `/assets/catalog.json` and `/discovery.json`: compare published timestamps, IDs/counts, download flags and notices with the deployed data, then check home/catalog images and links. Report the commit, workflow/deployment result and any unresolved publication issue; a successful push alone is not publication verification.

The current workflow publishes an Actions Pages artifact. Do not also copy files to `gh-pages`; older branch-deployment instructions in `website/README.md` are historical. If repository Pages settings disagree with the workflow, stop and resolve that configuration before claiming publication succeeded.
