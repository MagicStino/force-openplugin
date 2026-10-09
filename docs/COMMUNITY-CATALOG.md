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

## Private email notifications

The notification workflow sends new catalog proposals and maintainer applications only when configured. It uses these repository **Actions secrets**, never a public email address:

- `CATALOG_NOTIFY_TO`: recipient address.
- `CATALOG_SMTP_HOST`, `CATALOG_SMTP_PORT`: SMTP service; port 587 uses STARTTLS and 465 uses TLS.
- `CATALOG_SMTP_USER`, `CATALOG_SMTP_PASSWORD`: sender credentials (use an app password where required).
- `CATALOG_SMTP_FROM`: sender address authorized by that service.

Configure them under **Settings → Secrets and variables → Actions**. Without the complete settings, the action says notifications are not configured and sends nothing. A manual **Run workflow** sends a test message. Credentials and recipient addresses are not printed. The repository remains usable through GitHub notifications without SMTP.

The owner keeps control of merging and invitations. No multi-year availability or automatic acceptance is promised.
