#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
mkdir -p dist

readarray -t LOCK < <(python3 - <<'PY'
import json
x=json.load(open('config/sources.lock.json'))
for value in (x['kernel']['url'], x['kernel']['commit'],
              x['toolchain']['url'], x['toolchain']['commit'],
              x['toolchain']['directory'], x['toolchain']['tree']):
    print(value)
PY
)

if [[ ! -e kernel/.git ]]; then
  git init kernel
  git -C kernel remote add origin "${LOCK[0]}"
  git -C kernel fetch --depth=1 origin "${LOCK[1]}"
  git -C kernel checkout --detach FETCH_HEAD
fi
test "$(git -C kernel rev-parse HEAD)" = "${LOCK[1]}"

if [[ ! -e toolchain/.git ]]; then
  git init toolchain
  git -C toolchain remote add origin "${LOCK[2]}"
  git -C toolchain sparse-checkout init --cone
  git -C toolchain sparse-checkout set "${LOCK[4]}"
  git -C toolchain -c http.version=HTTP/1.1 fetch --filter=blob:none --depth=1 origin "${LOCK[3]}"
  git -C toolchain checkout --detach FETCH_HEAD
fi
test "$(git -C toolchain rev-parse HEAD)" = "${LOCK[3]}"
test "$(git -C toolchain rev-parse "HEAD:${LOCK[4]}")" = "${LOCK[5]}"
"toolchain/${LOCK[4]}/bin/clang" --version | tee dist/compiler.txt

# Slot 1 is already in use in this Lineage tree. Slots 6-8 are still reserved.
git -C kernel apply --check "$ROOT/patches/0001-sysvipc-kabi-padding-6-7-8.patch"
git -C kernel apply "$ROOT/patches/0001-sysvipc-kabi-padding-6-7-8.patch"

# Preserve the release expected by the installed vendor and SukiSU LKM modules.
# The changed source and configuration are identified separately in build.json.
printf '%s\n' '-g093e3da978e7' > kernel/.scmversion
git -C kernel diff > dist/source.patch
cp config/sources.lock.json dist/
