# 来源与许可

本项目原创构建脚本、配置和文档以 GPL-2.0-only 发布。`LICENSE` 包含 GNU GPL v2 正文。

| 组件 | 上游与固定版本 | 声明保留位置 |
|---|---|---|
| Linux / LineageOS 内核 | `LineageOS/android_kernel_xiaomi_sm8550`，`093e3da978e7b954d041a261d40975957c7fe6f1` | 完整源码归档中的 COPYING、LICENSES 与各源文件头 |
| SYSVIPC kABI 补丁 | `ravindu644/Droidspaces-OSS`，`64d53d17e765dad3028171204220f4d1134c7e37` | `patches/0001-sysvipc-kabi-padding-6-7-8.patch`，保留作者与 Signed-off-by |
| AnyKernel3 | `osm0sis/AnyKernel3`，`c072981836cd3ee46ad52a5f2cba76ecb927cb1b` | 刷机 ZIP 中的 LICENSE 与脚本版权声明 |
| Clang / LLVM 工具链 | AOSP prebuilts `9916fb51ccb914d62d35ad9a7b9b21d2ef046928` 下的 `clang-r563880c` | 构建时下载的工具链 NOTICE、MODULE_LICENSE 与源文件声明 |

上游组件继续适用各自的许可。构建过程不会将当前手机的厂商模块、启动分区备份或 root 模块二进制包含在内核 ZIP 中。

Release 的完整源码归档包括生成该内核所使用的修改后源码、配置与构建支持文件。`config/sources.lock.json` 记录所有固定来源，Release 的 `build.json` 记录构建代码提交和输入摘要。
