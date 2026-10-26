### AnyKernel3: socrates LineageOS 23.2 Droidspaces kernel
properties() { '
kernel.string=socrates 5.15.211 Droidspaces (LineageOS 23.2)
do.devicecheck=1
do.modules=0
do.systemless=0
do.cleanup=1
do.cleanuponabort=0
device.name1=socrates
supported.versions=16
supported.patchlevels=
supported.vendorpatchlevels=
'; }

BLOCK=boot;
IS_SLOT_DEVICE=1;
RAMDISK_COMPRESSION=auto;
PATCH_VBMETA_FLAG=0;
. tools/ak3-core.sh;

# The SukiSU LKM and its ramdisk are in init_boot, which this ZIP never opens.
split_boot;
flash_boot;
