# 首个成功构建结果

2026-10-26 20:29:56（北京时间），GitHub Actions 运行 **40314557379** 成功结束。内核编译与 CRC 比较阶段约 61 分钟，整个成功任务约 68 分钟。

- 私有仓库：[shark-wan/Kernel-socrates-DroidSpaces](https://github.com/shark-wan/Kernel-socrates-DroidSpaces)
- 成功运行：[40314557379](https://github.com/shark-wan/Kernel-socrates-DroidSpaces/actions/runs/40314557379)
- 构建代码提交：`c559d5203882a6d1c534baaee18258c1390039ad`
- 附件名：`socrates-droidspaces-5`
- 本机下载目录：`artifacts/run-40314557379/socrates-droidspaces-5/`

## 产物

| 文件 | 大小 | SHA256 |
|---|---:|---|
| `Image` | 49,138,176 bytes | `88205fe3a4e7298f6b3bc90f17763a047fad2b543f42566569b39c9e5cd42e50` |
| `socrates-lineage23.2-5.15.211-droidspaces.zip` | 25,486,375 bytes | `f921d60a0bc6282eee0633637f5271cff208cc6f3e2f988d772791ca60b41bdb` |

独立 Image 与 ZIP 内 Image 逐字节一致；下载文件 SHA256 已在 Windows 本机重新计算，均与云端 SHA256SUMS 匹配。内核 release 为 `5.15.211-g093e3da978e7`。

附件同时保留实际配置、配置差异、源码补丁、编译器与源码固定信息、Module.symvers、ABI 报告和构建日志。

## ABI 结果

- 输入：从本机采集的 **401 个 vendor_dlkm 模块**。
- 匹配：**3971 个不同导入符号**的 CRC 匹配。
- CRC 不匹配：**0**。
- 未能分类的缺失导入：**0**。
- 新构建 Module.symvers 之外的 **573 个符号**已确认由现有外部厂商模块导出；本轮不替换这些模块。
- init_boot 的 SukiSU LKM 没有导入 CRC 记录，其启动后实际 root 功能需要另行确认。

该结果证明已检查接口的 CRC 与现有模块匹配，不能替代设备启动和实际容器运行验证。

## 新增功能

实际生成配置已启用 SYSVIPC、POSIX_MQUEUE、IPC_NS、PID_NS、DEVTMPFS、USER_NS、addrtype、macvlan、IPv6 NAT、IP set、日志/防火墙推荐项及 tmpfs ACL/xattr。

Full LTO、CFI、SHADOW_CALL_STACK、KASAN_HW_TAGS、BTF、MODVERSIONS 等配置保持当前实机设置。CPU quota 与 PID 数限制保持关闭。AnyKernel3 只替换当前槽 boot 内核，保留 init_boot、vendor_boot、dtbo 和现有模块。

## 后续运行验证

构建完成时尚未刷写。随后经用户授权，已成功刷入、重启并完成 root、模块、硬件服务枚举与 Droidspaces Requirements 检查，见 [刷机与启动验证](flash-result-2026-10-26.md)。发行版容器启动/联网尚待下一阶段。

当前槽 `_b` 的原始 boot、init_boot、vendor_boot、dtbo 已备份在本机 `backups/5.15.211-g093e3da978e7_b/`，不上传 Git。
