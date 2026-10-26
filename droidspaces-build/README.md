# K60Prosocrates-Kernel-DroidSpaces

REDMI K60 Pro（socrates）的 DroidSpaces 适配内核、补丁与 GitHub Actions 构建脚本。

[下载 Release](https://github.com/shark-wan/K60Prosocrates-Kernel-DroidSpaces/releases/latest) · [完整内核源码](https://github.com/shark-wan/K60Prosocrates-Kernel-DroidSpaces/tree/kernel-source) · [构建流程](https://github.com/shark-wan/K60Prosocrates-Kernel-DroidSpaces/actions) · [实机验证](docs/flash-result-2026-10-26.md)

本项目针对 **LineageOS 23.2 / Android 16 / `5.15.211-g093e3da978e7`** 的实机制作 Droidspaces 内核。研究日期：2026-10-26。电脑只需 Windows、ADB、Git 和 GitHub CLI；Linux 编译发生在 GitHub Actions runner。

选用与实机对应的 LineageOS 内核提交，保留实机配置、厂商模块和 SukiSU LKM root 方式，加入 Droidspaces 官方 SYSVIPC kABI 补丁与 GKI 配置。详细依据见 [调研报告](docs/research-2026-10-26.md)。

**已成功构建并刷入实机。** 运行 `40314557379` 的产物已写入 boot_b，手机正常启动，390 个模块与刷前一致，root 正常，Droidspaces 必需项和推荐项全部通过。详见 [刷机与启动验证](docs/flash-result-2026-10-26.md)。构建阶段 401 个厂商模块的 3971 个可比较导入符号 CRC 匹配，0 个不匹配，见 [成功构建记录](docs/build-result-2026-10-26.md)。

## 构建

1. 本机的 `config/device-baseline.config` 与 `evidence/vendor-module-versions.json` 已通过 root ADB 采集。
2. 打开 GitHub **Actions → Build socrates Droidspaces kernel → Run workflow**。修改构建相关文件并推送 main 也会触发。
3. 下载运行页面的 `socrates-droidspaces-N` artifact。成功产物包含：
   - `Image`：原始 arm64 内核。
   - `socrates-lineage23.2-5.15.211-droidspaces.zip`：仅替换当前槽 boot 内核的 AnyKernel3 包。
   - `kernel.config`、`config.diff`、`Module.symvers`、`abi-report.json`、`source.patch`、`build.json`、`SHA256SUMS` 和构建日志。

工作流固定内核、工具链、补丁和 AnyKernel3 提交；实际使用 Clang **r563880c / 21.0.0**，保持实机 Full LTO、CFI、MTE/KASAN、MODVERSIONS 等配置。正常的 GitHub artifact 在失败时也会保存诊断文件；只有包含 Image、ZIP、build.json 且 workflow 成功的 artifact 才是完整产物。

Windows 也可直接通过 gh 下载成功构建的附件：

```powershell
gh release download --repo shark-wan/K60Prosocrates-Kernel-DroidSpaces --pattern '*.zip' --dir artifacts
gh run list --repo shark-wan/K60Prosocrates-Kernel-DroidSpaces
gh run download <成功运行的ID> --repo shark-wan/K60Prosocrates-Kernel-DroidSpaces --dir artifacts
```

## 源码与发布

main 分支公开构建脚本、固定来源、完整实机配置、改动补丁和验证记录；kernel-source 分支提供完整修改后内核源码。Release 同时提供 AnyKernel3 ZIP、原始 Image、完整源码归档、构建记录与 SHA256SUMS。源码归档与 kernel-source 分支的 Git tree 一致，包含对应版本的完整文件、实际 `.config`、`.scmversion` 和构建脚本快照，便于独立获取与复现。

如需重新导出源码归档，可在下载固定来源与已完成构建产物后运行：

```powershell
python scripts/package_source.py --archive .cache/kernel-source.tar.gz --artifact-dir artifacts/run-40314557379/socrates-droidspaces-5 --output-dir artifacts/public-v1.0.0
```

首版 Release 的二进制直接来自成功构建 `40314557379`，与已刷入手机并验证的 Image 相同。旧构建链接指向最初的私有构建仓库，仅作为历史来源记录；公开下载与后续构建使用本仓库。

## 更新实机采集

```powershell
python scripts/capture_device.py --adb C:/path/to/adb.exe --backup
```

脚本只读取手机；`--backup` 将当前槽 boot、init_boot、vendor_boot、dtbo 复制到本机被 Git 忽略的 `backups/`。采集其他 ROM 后，需同步审核 `sources.lock.json`、补丁 padding 和模块 ABI，不能只替换配置文件。

## 当前范围

此 ZIP 针对上述实机 ROM，不能据此宣称覆盖原厂 HyperOS 或其他 Lineage 版本。AnyKernel3 只处理 boot，保留 init_boot 内的 SukiSU LKM 和 vendor 驱动分区。本机验证方式为使用 ZIP 内同一 Image 重打包当前 boot 后刷入；尚未直接执行 ZIP 安装流程，也尚未创建发行版容器。CPU quota 和 PID 数限制保持未启用。

Droidspaces 应优先使用 **ext4 sparse image rootfs**：实机 `/data` 是 F2FS，直接将目录作为 Docker overlay2 或 volatile 模式的底层文件系统有兼容性问题。默认保留 SELinux Enforcing，由 Droidspaces 安装流程加载所需规则。

## 来源与授权

本项目原创构建脚本与配置采用 GPL-2.0-only。内核来自 LineageOS；SYSVIPC 补丁来自 ravindu644/Droidspaces-OSS，补丁作者与签名保留于 `patches/`；刷机模板来自 osm0sis/AnyKernel3。固定提交和来源 URL 见 `config/sources.lock.json`。许可正文见 `LICENSE`，上游组件保留各自许可与版权声明，见 [NOTICE](NOTICE.md)。
