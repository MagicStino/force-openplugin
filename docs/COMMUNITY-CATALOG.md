# Community catalog: suggest, support and maintain

## Suggest or support a plugin

1. [Search existing catalog proposals](https://github.com/MagicStino/force-openplugin/issues?q=is%3Aissue+%22%5BCatalog%5D%22).
2. If it already exists, add a **👍 reaction** to the opening post. Share a useful test report in a comment: device, firmware version, plugin version, what you tried, and the result.
3. Otherwise use [Submit a community plugin](https://github.com/MagicStino/force-openplugin/issues/new?template=plugin-submission.yml). Supply the public repository URL and description. A GitHub account is required.

Reactions show community interest. They do not automatically include a plugin, authorize downloads or establish that a package is safe. Reports remain attributed to their authors.

## Help maintain it

[Volunteer as a catalog maintainer](https://github.com/MagicStino/force-openplugin/issues/new?template=maintainer-application.yml). Metadata review, package review, documentation and device testing are all useful. Anyone can propose a pull request or comment without repository write access. The owner chooses trusted reviewers and grants access separately; applications do not trigger invitations automatically.

## Accept a proposal with one workflow

For repository maintainers with Actions write access:

1. Review the issue's repository, license, root `openplugin.json` and device reports. Check the package contract before enabling a download.
2. Open **Actions → Accept catalog submission → Run workflow** and enter the proposal's issue number.
3. Leave **Enable reviewed package downloads** unchecked to publish a source-only listing. Check it only after reviewing the portable ARMv7 package/install contract. Votes alone are insufficient.

The action reads the **Public project URL** field, validates the repository's root manifest, adds it to `catalog/sources.json` and opens a pull request. Review and merge that pull request. It does not execute or install a plugin and does not edit firmware. Changes to the source list and manifest format are checked by the catalog contribution workflow. If repository policy blocks Actions from creating a pull request, the action fails visibly and its branch can be used to open one manually.

Once merged, the catalog workflow fetches metadata and deploys both the device JSON and website cards. Users then tap **Refresh catalog** on their device. The current workflow runs every six hours and on source-list changes. Submission issues are not ingested into the shared catalog automatically.

Already registered authors can update versions in `openplugin.json`; put the newest usable package first. Repositories already in sd88me's upstream catalog must update that upstream entry, which takes precedence. Invalid or missing manifests appear as source notices and cannot create download actions.

## GitHub notifications

Use **Watch → Custom → Issues and Pull requests → Apply** on this repository. New plugin submissions and maintainer applications arrive as Issues; acceptance proposals arrive as pull requests. Read and manage them in [GitHub Notifications](https://github.com/notifications).

GitHub controls delivery through your personal notification preferences. No sender account, SMTP credentials or public recipient address is needed. Notifications inform reviewers; they do not automatically accept a plugin.

The owner keeps control of merging and invitations. No multi-year availability or automatic acceptance is promised.
