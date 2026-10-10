#!/usr/bin/env bash
# One entry point: fetch pinned source/tools, build native UI, build selected candidates.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
usage() {
  echo "Usage: bash build.sh Force.img MPC.img output-directory [owner-ed25519.pub]" >&2
  echo "   or: bash build.sh --device force|mpc-gen1 stock.img output-directory [owner-ed25519.pub]" >&2
  exit 2
}
DEVICE=both
SSH_KEY=""
if [ "${1:-}" = "--device" ]; then
  [ "$#" -eq 4 ] || [ "$#" -eq 5 ] || usage
  DEVICE="$2"
  case "$DEVICE" in force|mpc-gen1) ;; *) usage ;; esac
  SINGLE_INPUT="$(realpath "$3")"
  OUTPUT="$(realpath -m "$4")"
  SSH_KEY="${5:-}"
else
  [ "$#" -eq 3 ] || [ "$#" -eq 4 ] || usage
  FORCE_INPUT="$(realpath "$1")"
  MPC_INPUT="$(realpath "$2")"
  OUTPUT="$(realpath -m "$3")"
  SSH_KEY="${4:-}"
fi
for tool in python3 git debugfs e2fsck gcc readelf; do
  command -v "$tool" >/dev/null || { echo "Missing build dependency: $tool" >&2; exit 2; }
done
mkdir -p "$ROOT/.deps" "$OUTPUT"
python3 -m venv "$ROOT/.deps/venv"
"$ROOT/.deps/venv/bin/python" -m pip install -r "$ROOT/requirements-build.txt"
"$ROOT/.deps/venv/bin/python" -m playwright install chromium
"$ROOT/.deps/venv/bin/python" - "$ROOT" <<'PY'
import json, pathlib, subprocess, sys
root = pathlib.Path(sys.argv[1])
for name, dep in json.loads((root / 'dependencies.json').read_text()).items():
    dest = root / '.deps' / name
    if not dest.exists():
        subprocess.run(['git', 'clone', dep['url'], str(dest)], check=True)
        subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', dep['commit']], check=True)
    head = subprocess.check_output(['git', '-C', str(dest), 'rev-parse', 'HEAD'], text=True).strip()
    if head != dep['commit']:
        raise SystemExit(f'{dest}: expected pinned commit {dep["commit"]}; refusing to reset existing checkout')
PY
"$ROOT/.deps/venv/bin/python" -m unittest discover -s "$ROOT/tests" -v
gcc -O1 -fsanitize=address,undefined -fno-omit-frame-pointer "$ROOT/tests/test_native.c" -lpthread -ldl -lm -o "$ROOT/.deps/test-native"
ASAN_OPTIONS=detect_leaks=0 "$ROOT/.deps/test-native"
SSH_ARGS=()
if [ -n "$SSH_KEY" ]; then SSH_ARGS=(--ssh-key "$(realpath "$SSH_KEY")"); fi
"$ROOT/.deps/venv/bin/python" "$ROOT/tools/build_native.py" "${SSH_ARGS[@]}"
"$ROOT/.deps/venv/bin/python" "$ROOT/tools/verify_skin.py" "$ROOT/build/native" "$OUTPUT/preview"
if [ "$DEVICE" = both ] || [ "$DEVICE" = force ]; then
  "$ROOT/.deps/venv/bin/python" "$ROOT/tools/build.py" build "${FORCE_INPUT:-$SINGLE_INPUT}" --device force --native "$ROOT/build/native/payload" --output "$OUTPUT/Force-3.9.1-openplugin-v0.8-update.img"
fi
if [ "$DEVICE" = both ] || [ "$DEVICE" = mpc-gen1 ]; then
  "$ROOT/.deps/venv/bin/python" "$ROOT/tools/build.py" build "${MPC_INPUT:-$SINGLE_INPUT}" --device mpc-gen1 --native "$ROOT/build/native/payload" --output "$OUTPUT/MPC-3.9.1-Gen1-openplugin-v0.8-update.img"
fi
echo 'Candidates built and structurally checked. See docs/TESTING.md for hardware validation scope.'
