"""Turn one catalog proposal into a validated source-list change; never execute packages."""
import argparse, json, os, re, sys
from pathlib import Path
from catalog_bridge import read_json, validate_manifest, REPO

ROOT = Path(__file__).resolve().parents[1]

def proposal_repository(issue):
    if not str(issue.get('title', '')).startswith('[Catalog]') or 'pull_request' in issue:
        raise ValueError('Choose a catalog submission issue')
    body = issue.get('body') or ''
    match = re.search(r'^### Public project URL\s*\n+([^\n]+)', body, re.M)
    if not match:
        raise ValueError('Missing Public project URL field; use the submission form')
    url = match.group(1).strip().rstrip('/')
    match = re.fullmatch(r'https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', url)
    if not match or not REPO.fullmatch(match.group(1)):
        raise ValueError('Use a public GitHub repository URL, without a file or query')
    return match.group(1)

def accept(number, reviewed=False, fetch=read_json, root=ROOT):
    repository = os.environ.get('GITHUB_REPOSITORY', 'MagicStino/force-openplugin')
    if repository != 'MagicStino/force-openplugin' or number <= 0:
        raise ValueError('Invalid repository or issue number')
    issue = fetch(f'https://api.github.com/repos/{repository}/issues/{number}')
    repo = proposal_repository(issue)
    info = fetch('https://api.github.com/repos/' + repo)
    if info.get('private') or info.get('archived'):
        raise ValueError('Repository must be public and active')
    import urllib.parse
    branch = urllib.parse.quote(info.get('default_branch', 'main'), safe='')
    manifest = validate_manifest(fetch(f'https://raw.githubusercontent.com/{repo}/{branch}/openplugin.json'), repo)
    if reviewed and not manifest.get('packages'):
        raise ValueError('There is no declared package to enable')
    path = root / 'catalog/sources.json'
    cfg = json.loads(path.read_text())
    cfg['repositories'] = sorted(set(cfg['repositories']) | {repo})
    if reviewed:
        cfg['reviewed_manifest_repositories'] = sorted(set(cfg['reviewed_manifest_repositories']) | {repo})
    path.write_text(json.dumps(cfg, indent=2) + '\n')
    return repo

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--issue', type=int, required=True)
    p.add_argument('--reviewed-package', action='store_true')
    a = p.parse_args()
    try:
        repo = accept(a.issue, a.reviewed_package)
    except Exception as e:
        sys.exit('Submission not accepted: ' + str(e))
    print('Validated repository:', repo)
