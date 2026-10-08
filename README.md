# Force OpenPlugin

Development target: **3.9.1.1-openplugin**, based on the user's Force 3.9.1 update.
This is a project version only. The firmware's version encoding has not been
inspected and no firmware version fields have been changed.

## Current status

The repository was empty at inspection on 2026-10-08. The previously uploaded
`Force-3.9.1-update.img` is not available in this workspace or the referenced
conversation's accessible attachments. No Force module API, loader integration,
browser implementation, signing chain or target hardware has been validated.
There is currently **no custom firmware image and no flashable release**.

## Reproducible inspection

Requires Python 3.10 or newer; no third-party packages, root or mounting needed.

```sh
python3 tools/build.py inspect /path/to/Force-3.9.1-update.img --output build/inspection.json
python3 tools/build.py build /path/to/Force-3.9.1-update.img
python3 -m unittest discover -s tests -v
```

Inspection reads the input without changing it, computes its SHA-256 and records
its size and first 64 bytes. Output is deterministic for identical input bytes.
Recognized magic bytes are hints only, not validated container identification.

The build command deliberately fails without emitting an IMG: no verified
firmware adapter exists yet. Renaming or copying stock firmware is not a custom
build. The source repository does not need or contain a prebuilt IMG.

## Work needed before an image can be produced

1. Supply the exact stock image and record its hash and provenance.
2. Inspect the container, payloads, CPU/ABI, version fields, integrity checks,
   signatures and update/boot verification path using static analysis first.
3. Recover the intended module-browser requirements and determine whether a
   supported loader/API exists. Define module format, discovery paths, UI,
   audio/MIDI lifecycle and compatibility from evidence.
4. Implement and test an adapter and module/browser integration against those
   findings. Preserve cryptographic/security controls. If vendor signing is
   required and unavailable, report that limitation and stop image production.
5. Pin toolchain/dependency versions and build parameters, then compare hashes
   from two clean builds. Validate container and payload integrity separately
   from signature validity, installation, boot and runtime behavior.
6. Validate on suitable hardware with a recovery procedure before describing
   any artifact as flashable.

Neither signing requirements nor their absence can be inferred from a filename
or magic bytes. This project does not bypass signature checks.

## Artifact publication

No IMG is committed or published at this stage. Before publishing a future
validated build, check the current GitHub file and release-asset limits and
firmware redistribution rights. Prefer a versioned release asset when it is
inappropriate to put the binary in Git; publish SHA-256, source commit,
input hash, exact build command, pinned tool versions and validation results
with it. If redistribution is unavailable, distribute source and instructions
that accept a user-provided stock image instead.
