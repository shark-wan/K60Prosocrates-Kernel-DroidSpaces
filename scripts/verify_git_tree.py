"""Verify extracted compiler contents against an upstream Git tree ID.

Gitiles tarballs carry generation timestamps, so their compressed SHA256 is not
stable across requests. Git blob/tree IDs authenticate content, names and modes
without depending on archive timestamps. Requires only Python's standard library.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import tarfile


def git_hash(kind: str, size: int, chunks) -> bytes:
    digest = hashlib.sha1(f"{kind} {size}\0".encode())
    for chunk in chunks:
        digest.update(chunk)
    return digest.digest()


def file_hash(stream, size: int) -> bytes:
    return git_hash("blob", size, iter(lambda: stream.read(1024 * 1024), b""))


def tree_hash(entries: dict) -> bytes:
    payload = bytearray()
    ordered = sorted(entries.items(), key=lambda x: os.fsencode(x[0]) +
                     (b"/" if isinstance(x[1], dict) else b""))
    for name, item in ordered:
        mode, digest = ("40000", tree_hash(item)) if isinstance(item, dict) else item
        payload.extend(mode.encode() + b" " + os.fsencode(name) + b"\0" + digest)
    return git_hash("tree", len(payload), [payload])


def directory_entries(path: Path) -> dict:
    entries = {}
    for entry in os.scandir(path):
        if entry.is_symlink():
            target = os.fsencode(os.readlink(entry.path))
            entries[entry.name] = ("120000", git_hash("blob", len(target), [target]))
        elif entry.is_dir(follow_symlinks=False):
            entries[entry.name] = directory_entries(Path(entry.path))
        elif entry.is_file(follow_symlinks=False):
            info = entry.stat()
            with open(entry.path, "rb") as stream:
                entries[entry.name] = ("100755" if info.st_mode & 0o111 else "100644",
                                       file_hash(stream, info.st_size))
        else:
            raise ValueError(f"Unsupported compiler file: {entry.path}")
    return entries


def archive_entries(path: Path) -> dict:
    entries = {}
    with tarfile.open(path, "r|gz") as archive:
        for member in archive:
            parts = PurePosixPath(member.name).parts
            if not parts:
                continue
            node = entries
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            if member.isdir():
                node.setdefault(parts[-1], {})
            elif member.issym():
                target = os.fsencode(member.linkname)
                node[parts[-1]] = ("120000", git_hash("blob", len(target), [target]))
            elif member.isfile():
                with archive.extractfile(member) as stream:
                    node[parts[-1]] = ("100755" if member.mode & 0o111 else "100644",
                                      file_hash(stream, member.size))
            else:
                raise ValueError(f"Unsupported archive member: {member.name}")
    return entries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("expected")
    parser.add_argument("--archive", action="store_true")
    args = parser.parse_args()
    actual = tree_hash((archive_entries if args.archive else directory_entries)(args.path)).hex()
    print(f"Git tree: {actual}")
    if actual != args.expected:
        raise SystemExit(f"Expected Git tree: {args.expected}")
