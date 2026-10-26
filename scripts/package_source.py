"""Package the exact modified kernel source and a browsable Git snapshot.

Requires Python 3 and Git. This packages existing build inputs, without compiling.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--git-snapshot", type=Path)
    args = parser.parse_args()
    args.archive = args.archive.resolve()
    args.artifact_dir = args.artifact_dir.resolve()
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / "config/sources.lock.json").read_text(encoding="utf-8"))
    assert sha256(args.archive) == lock["kernel"]["archive_sha256"]
    build = json.loads((args.artifact_dir / "build.json").read_text(encoding="utf-8"))
    assert sha256(args.artifact_dir / "Image") == build["hashes"]["dist/Image"]
    expected_zip = "f921d60a0bc6282eee0633637f5271cff208cc6f3e2f988d772791ca60b41bdb"
    kernel_zip = args.artifact_dir / "socrates-lineage23.2-5.15.211-droidspaces.zip"
    assert sha256(kernel_zip) == expected_zip

    changed = {"include/linux/sched.h", "arch/arm64/configs/gki_defconfig"}
    with tempfile.TemporaryDirectory(prefix="socrates-source-") as temporary:
        scratch = Path(temporary)
        subprocess.run(["git", "init", "-q", str(scratch)], check=True)
        with tarfile.open(args.archive, "r|gz") as archive:
            for member in archive:
                relative = "/".join(PurePosixPath(member.name).parts[1:])
                if relative in changed:
                    target = scratch / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
        subprocess.run(["git", "-C", str(scratch), "apply", "--check",
                        str(args.artifact_dir / "source.patch")], check=True)
        subprocess.run(["git", "-C", str(scratch), "apply",
                        str(args.artifact_dir / "source.patch")], check=True)
        replacements = {name: (scratch / name).read_bytes() for name in changed}
    replacements[".config"] = (args.artifact_dir / "kernel.config").read_bytes()
    replacements[".scmversion"] = b"-g093e3da978e7\n"
    replacements["DROIDSPACES_BUILD.md"] = (
        "# socrates DroidSpaces source snapshot\n\n"
        f"Upstream kernel commit: {lock['kernel']['commit']}\n\n"
        "The source.patch from the validated build has been applied. .config is "
        "the actual running configuration. .scmversion preserves module vermagic.\n\n"
        "Pinned compiler, source references, build scripts and configuration are "
        "included under droidspaces-build/. The original build code commit is "
        f"{build['ci_commit']}.\n\n"
        "For the automated build, use droidspaces-build/scripts/prepare-runner.sh, "
        "prepare.sh, build.sh and package.sh on an Ubuntu GitHub Actions runner, "
        "as described in droidspaces-build/README.md. Full LTO, CFI and HW_TAGS "
        "remain enabled.\n\n"
        "All upstream copyright and license files are retained.\n"
    ).encode()

    tracked = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"])
    for raw in tracked.split(b"\0"):
        if not raw:
            continue
        name = os.fsdecode(raw).replace("\\", "/")
        replacements["droidspaces-build/" + name] = (ROOT / name).read_bytes()
    replacements["droidspaces-build/validated-build.json"] = (
        args.artifact_dir / "build.json").read_bytes()

    snapshot = None
    if args.git_snapshot:
        args.git_snapshot = args.git_snapshot.resolve()
        if args.git_snapshot.exists():
            raise SystemExit(f"Snapshot directory already exists: {args.git_snapshot}")
        subprocess.run(["git", "init", "--bare", "--initial-branch=kernel-source",
                        str(args.git_snapshot)], check=True)
        snapshot = subprocess.Popen(
            ["git", "-C", str(args.git_snapshot), "fast-import", "--quiet"],
            stdin=subprocess.PIPE)
        stamp = int(time.time())
        message = ("Import complete validated socrates DroidSpaces kernel source\n\n"
                   f"Upstream-Commit: {lock['kernel']['commit']}\n"
                   f"Build-Code-Commit: {build['ci_commit']}\n"
                   "Original source copyright and license notices are preserved.\n").encode()
        snapshot.stdin.write(("commit refs/heads/kernel-source\n"
                              f"committer Codex <codex@users.noreply.github.com> {stamp} +0800\n"
                              f"data {len(message)}\n").encode() + message + b"\n")

    destination = args.output_dir / "socrates-5.15.211-droidspaces-source.tar.gz"
    prefix = "socrates-5.15.211-droidspaces-source"
    count = 0
    with tarfile.open(destination, "w:gz", compresslevel=6) as output:
        def add_file(name: str, data: bytes, mode: int = 0o644,
                     linkname: str | None = None) -> None:
            nonlocal count
            info = tarfile.TarInfo(prefix + "/" + name)
            info.mtime = 1789799507
            info.mode = mode
            if linkname is not None:
                info.type = tarfile.SYMTYPE
                info.linkname = linkname
                output.addfile(info)
                git_data = os.fsencode(linkname)
                git_mode = "120000"
            else:
                info.size = len(data)
                output.addfile(info, io.BytesIO(data))
                git_data = data
                git_mode = "100755" if mode & 0o111 else "100644"
            if snapshot:
                path = json.dumps(name, ensure_ascii=True)
                snapshot.stdin.write(f"M {git_mode} inline {path}\ndata {len(git_data)}\n".encode())
                snapshot.stdin.write(git_data)
                snapshot.stdin.write(b"\n")
            count += 1

        with tarfile.open(args.archive, "r|gz") as archive:
            for member in archive:
                name = "/".join(PurePosixPath(member.name).parts[1:])
                if not name or name in replacements or member.isdir():
                    continue
                if member.issym():
                    add_file(name, b"", member.mode, member.linkname)
                elif member.isfile():
                    add_file(name, archive.extractfile(member).read(), member.mode)
                else:
                    raise ValueError(f"Unsupported source archive member: {name}")
        for name, data in sorted(replacements.items()):
            add_file(name, data)
    if snapshot:
        snapshot.stdin.write(b"\ndone\n")
        snapshot.stdin.close()
        if snapshot.wait() != 0:
            raise SystemExit("Git source snapshot import failed")
        print("Git source snapshot:", subprocess.check_output(
            ["git", "-C", str(args.git_snapshot), "rev-parse", "kernel-source"],
            text=True).strip(), flush=True)

    for name in (kernel_zip.name, "Image"):
        shutil.copyfile(args.artifact_dir / name, args.output_dir / name)
    info_path = args.output_dir / "socrates-5.15.211-droidspaces-build-info.zip"
    with zipfile.ZipFile(info_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.artifact_dir.iterdir()):
            if path.is_file() and path.name not in (kernel_zip.name, "Image"):
                archive.write(path, path.name)
        for name in ("evidence/flash-result.json", "evidence/droidspaces-after.txt",
                     "docs/flash-result-2026-10-26.md", "NOTICE.md"):
            archive.write(ROOT / name, name)
    paths = sorted(p for p in args.output_dir.iterdir()
                   if p.is_file() and p.name != "SHA256SUMS")
    (args.output_dir / "SHA256SUMS").write_text(
        "".join(f"{sha256(p)}  {p.name}\n" for p in paths), encoding="utf-8", newline="\n")
    print(f"Packaged {count} source files/links", flush=True)
    print((args.output_dir / "SHA256SUMS").read_text(), flush=True)


if __name__ == "__main__":
    main()
