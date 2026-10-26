# socrates DroidSpaces source snapshot

Upstream kernel commit: 093e3da978e7b954d041a261d40975957c7fe6f1

The source.patch from the validated build has been applied. .config is the actual running configuration. .scmversion preserves module vermagic.

Pinned compiler, source references, build scripts and configuration are included under droidspaces-build/. The original build code commit is c559d5203882a6d1c534baaee18258c1390039ad.

For the automated build, use droidspaces-build/scripts/prepare-runner.sh, prepare.sh, build.sh and package.sh on an Ubuntu GitHub Actions runner, as described in droidspaces-build/README.md. Full LTO, CFI and HW_TAGS remain enabled.

All upstream copyright and license files are retained.
