#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
mkdir -p dist

readarray -t LOCK < <(python3 - <<'PY'
import json
x=json.load(open('config/sources.lock.json'))
for value in (x['kernel']['archive_url'], x['kernel']['archive_sha256'],
              x['toolchain']['archive_url'], x['toolchain']['commit'],
              x['toolchain']['directory'], x['toolchain']['tree']):
    print(value)
PY
)

mkdir -p kernel toolchain/"${LOCK[4]}" .cache
curl -fL --retry 3 "${LOCK[0]}" -o .cache/kernel-source.tar.gz
printf '%s  %s\n' "${LOCK[1]}" .cache/kernel-source.tar.gz | sha256sum --check
tar -xzf .cache/kernel-source.tar.gz --strip-components=1 -C kernel
rm .cache/kernel-source.tar.gz

# Gitiles archives contain only the requested compiler directory. A sparse
# checkout still retains Git objects and exhausted the first hosted runner.
curl -fL --retry 3 "${LOCK[2]}" -o .cache/clang.tar.gz
sha256sum .cache/clang.tar.gz > dist/compiler-archive.sha256
tar -xzf .cache/clang.tar.gz -C "toolchain/${LOCK[4]}"
rm .cache/clang.tar.gz
python3 scripts/verify_git_tree.py "toolchain/${LOCK[4]}" "${LOCK[5]}"
python3 - <<'PY'
import json,urllib.request
x=json.load(open('config/sources.lock.json'))['toolchain']
url=f"{x['url']}/+/{x['commit']}/{x['directory']}/?format=JSON"
with urllib.request.urlopen(url,timeout=60) as response:
    tree=json.loads(response.read()[4:])['id']
assert tree==x['tree'], (tree,x['tree'])
PY
"toolchain/${LOCK[4]}/bin/clang" --version | tee dist/compiler.txt

cp kernel/include/linux/sched.h .cache/sched.h.original
cp kernel/arch/arm64/configs/gki_defconfig .cache/gki_defconfig.original

# Slot 1 is already in use in this Lineage tree. Slots 6-8 are still reserved.
patch --directory=kernel --strip=1 --batch --fuzz=0 --dry-run < patches/0001-sysvipc-kabi-padding-6-7-8.patch
patch --directory=kernel --strip=1 --batch --fuzz=0 < patches/0001-sysvipc-kabi-padding-6-7-8.patch

# Preserve the release expected by the installed vendor and SukiSU LKM modules.
# The changed source and configuration are identified separately in build.json.
printf '%s\n' '-g093e3da978e7' > kernel/.scmversion
diff -u --label a/include/linux/sched.h --label b/include/linux/sched.h \
  .cache/sched.h.original kernel/include/linux/sched.h > dist/source.patch || test "$?" -eq 1
cp config/sources.lock.json dist/
df -h .
du -sh kernel toolchain
