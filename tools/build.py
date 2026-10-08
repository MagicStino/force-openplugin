#!/usr/bin/env python3
"""Read-only firmware inventory; fail closed until an adapter is validated."""
import argparse
import hashlib
import json
from pathlib import Path

PROJECT_VERSION = "3.9.1.1-openplugin"

def inspect_image(path):
    digest = hashlib.sha256()
    size = 0
    with Path(path).open("rb") as source:
        header = source.read(64)
        digest.update(header)
        size += len(header)
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    if size == 0:
        raise ValueError("Input image is empty")
    hints = []
    for magic, name in [(b"PK\x03\x04", "ZIP"), (b"\x1f\x8b", "gzip"),
                        (b"hsqs", "SquashFS little-endian"), (b"\x7fELF", "ELF")]:
        if header.startswith(magic):
            hints.append(name)
    return {
        "schema_version": 1,
        "project_version": PROJECT_VERSION,
        "size_bytes": size,
        "sha256": digest.hexdigest(),
        "header_hex": header.hex(),
        "container_hints_unverified": hints,
        "firmware_version": None,
        "signature_status": "not inspected",
        "flash_validation": "not performed",
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inspect", "build"])
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.resolve() == args.image.resolve():
        parser.error("Output must not overwrite the input image")
    try:
        report = inspect_image(args.image)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Input error: {error}\n")
    if args.command == "build":
        parser.exit(2, "Build blocked: no validated Force firmware adapter, version encoding, "
                    "module integration or signing path. No IMG produced.\n")
    encoded = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")

if __name__ == "__main__":
    main()
