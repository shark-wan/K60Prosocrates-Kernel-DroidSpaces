#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
readarray -t AK3 < <(python3 - <<'PY'
import json
x=json.load(open('config/sources.lock.json'))['anykernel3']
print(x['url']); print(x['commit'])
PY
)
git init .cache/anykernel3
git -C .cache/anykernel3 remote add origin "${AK3[0]}"
git -C .cache/anykernel3 fetch --depth=1 origin "${AK3[1]}"
git -C .cache/anykernel3 checkout --detach FETCH_HEAD
cp dist/Image .cache/anykernel3/Image
cp config/anykernel.sh .cache/anykernel3/anykernel.sh
cp dist/build.json .cache/anykernel3/build.json
cd .cache/anykernel3
zip -r9 "$ROOT/dist/socrates-lineage23.2-5.15.211-droidspaces.zip" . -x '.git/*' '.github/*' 'README.md'
cd "$ROOT/dist"
sha256sum Image socrates-lineage23.2-5.15.211-droidspaces.zip > SHA256SUMS
