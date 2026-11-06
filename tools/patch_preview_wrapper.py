"""Manager-only wrapper hook for deferred storage discovery; no pixel controls."""
from pathlib import Path

def patch(source):
 s=Path(source).read_text()
 # Force skin lookup depends on the binary product name; keep PLUG_NAME unchanged.
 old='    case effGetParamDisplay: {'
 assert s.count(old)==1
 return s.replace(old, old+'\n        if(idx>=0&&idx<NPARAMS&&!strcmp(PARAMS[idx].key,"storage_warning"))eng_set(w,"storage_open","1");',1)
