#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
TOOLCHAIN_DIR=$(python3 -c "import json; print(json.load(open('config/sources.lock.json'))['toolchain']['directory'])")
export PATH="$ROOT/toolchain/$TOOLCHAIN_DIR/bin:$PATH"
export ARCH=arm64 LLVM=1 LLVM_IAS=1
export CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_COMPAT=arm-linux-gnueabi-
export KBUILD_BUILD_USER=socrates KBUILD_BUILD_HOST=github-actions
export KBUILD_BUILD_TIMESTAMP='Sat Sep 19 06:31:47 UTC 2026'
export KBUILD_BUILD_VERSION=1
JOBS="${JOBS:-$(nproc)}"
mkdir -p out dist

cp config/device-baseline.config out/.config

# Keep the official GKI defconfig and actual build config consistent.
# Unlike a blind fragment merge, olddefconfig will resolve all dependencies.
while IFS= read -r entry; do
  if [[ "$entry" =~ ^CONFIG_([A-Z0-9_]+)=y$ ]]; then
    kernel/scripts/config --file kernel/arch/arm64/configs/gki_defconfig --enable "${BASH_REMATCH[1]}"
    kernel/scripts/config --file out/.config --enable "${BASH_REMATCH[1]}"
  fi
done < config/droidspaces.config

make -C kernel O="$ROOT/out" olddefconfig

kernel/scripts/diffconfig config/device-baseline.config out/.config > dist/config.diff
cp out/.config dist/kernel.config
diff -u --label a/arch/arm64/configs/gki_defconfig --label b/arch/arm64/configs/gki_defconfig \
  .cache/gki_defconfig.original kernel/arch/arm64/configs/gki_defconfig >> dist/source.patch || test "$?" -eq 1

python3 - <<'PY'
from pathlib import Path
def read(path):
    return dict(line.split('=',1) for line in Path(path).read_text().splitlines()
                if line.startswith('CONFIG_') and '=' in line)
actual=read('out/.config')
wanted=read('config/droidspaces.config')
missing=[(name,actual.get(name),value) for name,value in wanted.items() if actual.get(name)!=value]
assert not missing, missing
baseline=read('config/device-baseline.config')
for name in ('CONFIG_MODVERSIONS','CONFIG_CFI_CLANG','CONFIG_LTO_CLANG_FULL',
             'CONFIG_KASAN_HW_TAGS','CONFIG_SHADOW_CALL_STACK','CONFIG_DEBUG_INFO_BTF',
             'CONFIG_MODULE_SIG_PROTECT','CONFIG_TARGET_PRODUCT_SOCRATES'):
    assert actual.get(name)==baseline.get(name)=='y', name
for name in ('CONFIG_CFS_BANDWIDTH','CONFIG_CGROUP_PIDS'):
    assert actual.get(name)==baseline.get(name), name
PY

make -C kernel O="$ROOT/out" -j"$JOBS" Image modules 2>&1 | tee dist/build.log
cp out/arch/arm64/boot/Image dist/Image
cp out/Module.symvers dist/Module.symvers
cp out/include/generated/utsrelease.h dist/
python3 scripts/check_module_abi.py dist/Module.symvers evidence/vendor-module-versions.json --report dist/abi-report.json

python3 - <<'PY'
import hashlib,json,os
from pathlib import Path
lock=json.load(open('config/sources.lock.json'))
release=Path('dist/utsrelease.h').read_text().split('"')[1]
assert release==lock['kernel']['release'], (release,lock['kernel']['release'])
info={'device':lock['device'],'kernel_release':release,'sources':lock,
      'ci_commit':os.environ.get('GITHUB_SHA'), 'ci_run_id':os.environ.get('GITHUB_RUN_ID'),
      'changes':'Droidspaces GKI config and SYSVIPC kABI padding 6/7/8; current LKM root retained',
      'hashes':{name:hashlib.sha256(Path(name).read_bytes()).hexdigest()
                for name in ('config/device-baseline.config','config/droidspaces.config',
                             'patches/0001-sysvipc-kabi-padding-6-7-8.patch','dist/Image')},
      'validation':'Built Image and imported symbol CRC comparison; device boot not tested'}
Path('dist/build.json').write_text(json.dumps(info,indent=2)+'\n')
PY
