"""Collect build inputs and optionally copy boot partitions. No device writes.

Usage (PowerShell): python scripts/capture_device.py --adb C:/path/to/adb.exe
The generated CRC inventory contains symbol names and checksums, not module code.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import gzip
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from elf_versions import module_versions

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial")
    parser.add_argument("--backup", action="store_true")
    args = parser.parse_args()
    adb = [args.adb] + (["-s", args.serial] if args.serial else [])

    def root(command: str) -> bytes:
        if "'" in command:
            raise ValueError("Remote command contains an unsupported quote")
        return subprocess.run(adb + ["exec-out", f"su -c '{command}'"],
                              check=True, stdout=subprocess.PIPE).stdout

    if root("id -u").strip() != b"0":
        raise SystemExit("ADB su is not root")
    device = root("getprop ro.product.device").decode().strip()
    if device != "socrates":
        raise SystemExit(f"Expected socrates, got {device!r}")
    config = gzip.decompress(root("cat /proc/config.gz")).decode()
    (ROOT / "config/device-baseline.config").write_text(config, encoding="utf-8", newline="\n")
    slot = root("getprop ro.boot.slot_suffix").decode().strip()
    if slot not in ("_a", "_b"):
        raise SystemExit(f"Unexpected slot suffix {slot!r}")
    summary = {
        "collected_date": datetime.now().date().isoformat(),
        "device": device,
        "kernel_release": root("uname -r").decode().strip(),
        "lineage_version": root("getprop ro.lineage.version").decode().strip(),
        "android_version": root("getprop ro.build.version.release").decode().strip(),
        "security_patch": root("getprop ro.build.version.security_patch").decode().strip(),
        "selinux": root("getenforce").decode().strip(),
        "active_slot": slot,
        "boot_partition_size": int(root(f"blockdev --getsize64 /dev/block/by-name/boot{slot}")),
    }
    modules = root("cat /proc/modules").decode()
    summary["loaded_modules"] = len(modules.splitlines())
    summary["root_module"] = [line.split()[0] for line in modules.splitlines()
                              if re.search("kernelsu|sukisu", line, re.I)]
    (ROOT / "evidence/device-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    archive_data = root("tar -cf - -C /vendor_dlkm/lib/modules .")
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    (cache / "vendor-modules.tar").write_bytes(archive_data)
    inventory = {}
    with tarfile.open(fileobj=io.BytesIO(archive_data)) as archive:
        for member in archive:
            if member.isfile() and member.name.endswith(".ko"):
                data = archive.extractfile(member).read()
                inventory[Path(member.name).name] = module_versions(data)
    if not inventory:
        raise SystemExit("No vendor modules captured")
    kernel_exports = []
    vendor_exports = []
    for line in root("cat /proc/kallsyms").decode().splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[2].startswith("__ksymtab_"):
            symbol = fields[2][len("__ksymtab_"):]
            (kernel_exports if len(fields) == 3 else vendor_exports).append(symbol)
    if not kernel_exports:
        raise SystemExit("No kernel export names in kallsyms; cannot classify missing symbols")
    payload = {"modules": inventory, "kernel_exports": sorted(set(kernel_exports)),
               "vendor_exports": sorted(set(vendor_exports))}
    (ROOT / "evidence/vendor-module-versions.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.backup:
        backups = ROOT / "backups" / (summary["kernel_release"] + slot)
        backups.mkdir(parents=True, exist_ok=True)
        for partition in ("boot", "init_boot", "vendor_boot", "dtbo"):
            image = root(f"cat /dev/block/by-name/{partition}{slot}")
            (backups / f"{partition}{slot}.img").write_bytes(image)
            print(f"Saved {partition}{slot}: {len(image)} bytes")
    print(json.dumps(summary, indent=2))
    print(f"Captured import CRCs for {len(inventory)} vendor modules")


if __name__ == "__main__":
    main()
