# 刷机与启动验证结果

2026-10-26，在用户明确授权后，将已构建的 Droidspaces 内核刷入本机活动槽 **boot_b**。写入前，boot、init_boot、vendor_boot、dtbo 四个分区的 SHA256 均与已有备份一致。

## 写入内容

以当前 boot_b 为模板，用已固定版本 AnyKernel3 包中的 magiskboot 解包，将 kernel 替换为 Actions 运行 `40314557379` 的 Image，再重新打包。

- 新 boot 镜像：`artifacts/flash-20261026/boot-droidspaces.img`
- 大小：201326592 bytes，与 boot_b 分区一致。
- SHA256：`15d28dbba19a469790f24301652bbeff3430c4f196f92be534badc88f4e7d0c1`
- 内核 SHA256：`88205fe3a4e7298f6b3bc90f17763a047fad2b543f42566569b39c9e5cd42e50`
- 写入时间：2026-10-26 22:05:53（北京时间）。

重新打包后的 header v4、Android 版本、安全补丁标识、空 ramdisk、启动参数均保持原值；内核与 CI Image 逐字节一致，AVB 元数据随新镜像更新。仅写入 boot_b。写入后回读整个分区，其 SHA256 与待刷镜像一致；init_boot_b、vendor_boot_b、dtbo_b 的 SHA256 保持原值。

## 启动结果

重启后约 20 秒恢复 ADB，约 25 秒报告 `sys.boot_completed=1`。活动槽仍是 `_b`。内核 release 为 `5.15.211-g093e3da978e7`；由于保留模块兼容所需的版本串和构建时间，确认新内核的方法是读取运行配置，而非只看 uname。

实机 `/proc/config.gz` 解压结果与 CI `kernel.config` 完全一致，SHA256 为 `194029f29d2b80164dac212bc15ab70675db54e29aa7e884796ac38a34cff55c`。

| 检查 | 结果 |
|---|---|
| 启动完成、活动槽 | 成功，`_b` |
| SukiSU LKM / su | kernelsu 已加载，`uid=0`，ksu SELinux 域 |
| SELinux | Enforcing |
| 已加载模块 | 刷前、刷后均为 390 个，名称集合相同，无缺失 |
| GPU | SurfaceFlinger 报告 Qualcomm Adreno 740 / OpenGL ES 3.2 |
| 相机服务 | cameraserver 运行，枚举 3 个正常/公开相机设备 |
| 音频服务 | audioserver 运行，kalama-mtp-snd-card 已枚举 |
| 网络 | Wi-Fi 模块已加载，外网 ICMP 探测有响应；该探测不等于长期网络质量测试 |
| 内核日志 | 未发现 unknown symbol、符号版本冲突、CFI failure、panic 或 Oops 记录 |

日志中有 kernelsu 的无签名模块 taint 提示；模块实际已经加载，root 功能正常。这条信息不能误读成模块加载失败。上述硬件检查覆盖驱动/服务枚举，不代替实际拍照和扬声器收听。

## Droidspaces 结果

用官方 v7.0.0 aarch64 检查器在新内核执行 `check`：

- **MUST HAVE：全部通过。** 原来缺失的 PID namespace、IPC namespace 已通过。
- **RECOMMENDED：全部通过。** 原来缺失的 devtmpfs 已通过。
- 用户命名空间、macvlan、IPv6 NAT、memory limit、FUSE、TUN、OverlayFS、bridge、veth 等检查通过。
- CPU limit 与 process/PID limit 按既定 GKI 方案保持未启用，不影响必需项通过。

原始检查输出见 `evidence/droidspaces-after.txt`。本次完成刷机与内核运行检查；尚未安装 Droidspaces 应用/backend 或创建发行版容器。

## 本机留存

- 原分区备份：`backups/5.15.211-g093e3da978e7_b/`
- 新 boot 镜像与详细过程证据：`artifacts/flash-20261026/`
- 可提交的结果摘要：`evidence/flash-result.json`

原始分区镜像和完整 dmesg 保留在 Git 忽略目录，不上传仓库。
