# REDMI K60 Pro (socrates) · Droidspaces kernel

本项目针对 **LineageOS 23.2 / Android 16 / `5.15.211-g093e3da978e7`** 的实机制作 Droidspaces 内核。研究日期：2026-10-26。电脑只需 Windows、ADB、Git 和 GitHub CLI；Linux 编译发生在 GitHub Actions runner。

选用与实机对应的 LineageOS 内核提交，保留实机配置、厂商模块和 SukiSU LKM root 方式，加入 Droidspaces 官方 SYSVIPC kABI 补丁与 GKI 配置。详细依据见 [调研报告](docs/research-2026-10-26.md)。

## 构建

1. 本机的 `config/device-baseline.config` 与 `evidence/vendor-module-versions.json` 已通过 root ADB 采集。
2. 打开 GitHub **Actions → Build socrates Droidspaces kernel → Run workflow**。修改构建相关文件并推送 main 也会触发。
3. 下载运行页面的 `socrates-droidspaces-N` artifact。成功产物包含：
   - `Image`：原始 arm64 内核。
   - `socrates-lineage23.2-5.15.211-droidspaces.zip`：仅替换当前槽 boot 内核的 AnyKernel3 包。
   - `kernel.config`、`config.diff`、`Module.symvers`、`abi-report.json`、`source.patch`、`build.json`、`SHA256SUMS` 和构建日志。

工作流固定内核、工具链、补丁和 AnyKernel3 提交；实际使用 Clang **r563880c / 21.0.0**，保持实机 Full LTO、CFI、MTE/KASAN、MODVERSIONS 等配置。正常的 GitHub artifact 在失败时也会保存诊断文件；只有包含 Image、ZIP、build.json 且 workflow 成功的 artifact 才是完整产物。

## 更新实机采集

```powershell
python scripts/capture_device.py --adb C:/path/to/adb.exe --backup
```

脚本只读取手机；`--backup` 将当前槽 boot、init_boot、vendor_boot、dtbo 复制到本机被 Git 忽略的 `backups/`。采集其他 ROM 后，需同步审核 `sources.lock.json`、补丁 padding 和模块 ABI，不能只替换配置文件。

## 当前范围

此 ZIP 针对上述实机 ROM，不能据此宣称覆盖原厂 HyperOS 或其他 Lineage 版本。AnyKernel3 只处理 boot，保留 init_boot 内的 SukiSU LKM 和 vendor 驱动分区。实际启动与 Droidspaces 容器功能需在刷入后确认；构建成功和模块 CRC 匹配只证明各自覆盖的范围。

Droidspaces 应优先使用 **ext4 sparse image rootfs**：实机 `/data` 是 F2FS，直接将目录作为 Docker overlay2 或 volatile 模式的底层文件系统有兼容性问题。默认保留 SELinux Enforcing，由 Droidspaces 安装流程加载所需规则。

## 来源与授权

内核来自 LineageOS；SYSVIPC 补丁来自 ravindu644/Droidspaces-OSS，补丁作者与签名保留于 `patches/`；刷机模板来自 osm0sis/AnyKernel3。固定提交和来源 URL 见 `config/sources.lock.json`。Linux 内核许可见 `LICENSE`，各上游组件保留各自许可。
