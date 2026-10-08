#!/usr/bin/env python3
"""Use content hashes for upstream artwork IDs, independent of checkout path."""
import hashlib
import json
from pathlib import Path
import runpy
import sys

kit, config = map(Path, sys.argv[1:])
sys.path.insert(0, str(kit / 'tools'))
import skin_assets

def stable_look_id(look):
    if not look:
        return ''
    normalized = dict(look)
    for key in skin_assets.FILE_ATTRS:
        if key in normalized:
            normalized[key] = 'sha256:' + hashlib.sha256(Path(normalized[key]).read_bytes()).hexdigest()
    return hashlib.sha1(json.dumps(normalized, sort_keys=True).encode()).hexdigest()[:8]

skin_assets.look_id = stable_look_id
sys.argv = [str(kit / 'tools/gen_vst.py'), str(config)]
runpy.run_path(sys.argv[0], run_name='__main__')
