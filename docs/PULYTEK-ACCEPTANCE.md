# Maintainer acceptance: PulyTek submission #1

This records acceptance of [submission #1](https://github.com/MagicStino/force-openplugin/issues/1) as a downloadable **experimental** catalog entry. Package contract review is distinct from physical Force/MPC verification; hardware testing remains pending.

## Original acceptance evidence (historical)

- Public separate repository: https://github.com/MagicStino/pulytek . GPL-3.0-only, source and license notices retain Alberto Barrera / ABSounds and https://github.com/ABSounds/EQP-WDF-1A .
- Root community manifest: https://raw.githubusercontent.com/MagicStino/pulytek/main/openplugin.json . Validated repository identity, native ARMv7 portable effect target, device declarations, HTTPS release URL and checksum.
- Original reviewed package: v0.1.0-rc3, 17,165,088 bytes, SHA256 `b8f1b7f8699c58416b635df3bdc57d54eb5e0a9d9cbbe54f958b818840e21415`. Actual published ZIP downloaded and matched against both publisher JSON formats.
- ZIP contains `mpc-plugin.json`, ARM hard-float `.so`, native Akai skin/Q-Link assets, standard portable installation/removal scripts, license notices and complete corresponding source. Installer registration, settings backup and uninstall tested in an isolated fixture; no device installer ran during acceptance.
- DSP/native-host sanitizer checks, all 49 preset recalls/rendering at 44.1/48/96 kHz, ARM emulated loading/audio/state and skin bounds pass. [Native package and desktop VST3 CI](https://github.com/MagicStino/pulytek/actions/runs/38036183260) passed.
- At original acceptance, physical audio/CPU/touch/project reload validation was absent. Do not infer a device-tested record from those checks.

## Original acceptance workflow

1. Fetch the latest default branch and read the submission and publisher manifest. Recheck the ZIP checksum, manifest and installer contract before authorizing downloads.
2. Run `python3 tools/accept_submission.py --issue 1 --reviewed-package`. This adds `MagicStino/pulytek` to both `repositories` and `reviewed_manifest_repositories` in `catalog/sources.json`. The second list authorizes catalog downloads; omitting the flag creates a source-only entry. It authorizes subsequent valid releases from this repository too, so continue monitoring publisher updates.
3. Keep prerelease versions on the `beta` channel. The bridge now derives beta for version strings containing a prerelease suffix (a hyphen), including `0.1.0-rc3`; ordinary release versions remain stable. The native manager already displays a beta badge. Acceptance never invents hardware test reports.
4. Run `python3 -m unittest discover -s tests -p test_catalog_bridge.py`. Check stable and prerelease channel tests and source-only/reviewed publication paths.
5. Open and review a PR containing the registry change, channel fix, test and this record. Merge it after checks pass. This follows the normal acceptance workflow; no source scanner or publisher trust checks are bypassed.
6. The source-list merge triggers **Update community catalog and documentation cards**. It fetches the full upstream catalog and reviewed root manifests, writes `website/catalog.json`, `website/assets/catalog.json` and discovery metadata, then deploys GitHub Pages. Verify PulyTek has a ZIP download, exact hash/size and beta channel in the deployed full catalog and website cards.
7. Comment on and close submission #1 with the merged PR and validation status. Users tap **Refresh catalog**, find PulyTek in Effects and install the portable ZIP through the usual queue/restart flow. The separate GitHub Add source scanner only reads stable releases; main catalog inclusion is what makes rc3 available without that scanner.

## Rollback

Remove `MagicStino/pulytek` from `reviewed_manifest_repositories` to disable downloads while retaining a source-only listing, then refresh/deploy the catalog. Remove it from `repositories` too to unregister the project. The bridge preserves the previous catalog on primary-source failure or unexpected catalog shrink; investigate failures rather than replacing the full catalog with the publisher's single-plugin feed.

## Current release and community submission — 10 October 2026

[PulyTek 1.0.1](https://github.com/MagicStino/pulytek/releases/tag/v1.0.1) is in the published index on the stable release channel. The ZIP is 15,634,486 bytes, SHA256 `785743716456d9b7b9ed6e99959219bcaa72f8a6513788a2d423568afa8fb528`. The current upstream package checker passes with zero warnings. The owner reports working Force presets; no complete device/firmware tested record is supplied. Stable release metadata does not imply Verified hardware status.

[Community PR #278](https://github.com/sd88me/mpc-vst-plugins/pull/278) supersedes closed #276 and adds only the catalog manifest, with a version-pinned screenshot. It remains a submission until the community maintainers accept it.
