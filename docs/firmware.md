# 固件方案、构建与升级

底座为官方 OpenWrt 25.12.6、x86/64、UEFI、squashfs、APK 和 firewall4。使用 [底座来源锁](../sources.lock.json) 固定主仓库和 feeds。第三方插件、静态二进制和发布资产使用 [第三方来源锁](../custom-sources.lock.json)。扩展内核模块由同一源码和配置编译。使用 Linux x86_64 构建机，按 OpenWrt 官方文档安装依赖。[OpenWrt 构建依赖](https://openwrt.org/docs/guide-developer/toolchain/install-buildsystem)

## 从干净的构建树开始

以下入口准备官方 OpenWrt 和 Netdata 定制配方，同时选择 Docker、Compose、AdGuard Home 和 LuCI。Netdata 包由 OpenWrt 构建系统从锁定并校验的上游资产生成。

```sh
./scripts/prepare-openwrt.sh ./work/openwrt
cd ./work/openwrt
make -j"$(nproc)" download
make -j"$(nproc)" V=s
```

输出在 `bin/targets/x86/64/`，配套 APK 位于 `bin/packages/x86_64/`。检查文件完整性和 manifest 内的 `netdata - 2.12.3-r3`，生成并保存 SHA-256。首次启动用隔离的测试虚拟机。

## 扩展到完整网络界面配置

[完整网络界面配置](../profiles/network-ui.config) 记录了验收镜像的包选择，[菜单清单](components.md) 给出对应功能和来源。完整配置需要先从来源锁中获取第三方源码，将对应配方加入 `package/custom/`，并处理项目补丁。用 `make defconfig` 后对照配置和 manifest 检查每个目标包。

1. 在固定 OpenWrt 和 feeds 上依次准备 Argon、定制 LuCI、网络服务、VPN、Docker 和硬件相关模块。
2. Quickstart 页面及后端以 iStoreOS 25.12.6 2026110611 的发布资产为来源。使用 [提取脚本](../packages/istoreos-ui-2026110611/prepare-payload.py) 核验资产摘要，并按其 APK 文件归属提取。脚本参数依次为包含 `image.gz` 和解压得到的 `image.raw` 的目录、空输出目录和支持偏移量的 `unsquashfs` 路径。按上游许可管理这些发布文件。
3. 应用[补丁索引](../patches/README.md)中对应的适配。将 image-files/network-ui 的 LuCI 运行文件作为 OpenWrt 的 files/ overlay，使用同一 LuCI 构建树的 po2lmo 编译菜单翻译，再构建 EFI 镜像。验收计划包括包版本、UEFI 启动、IPv6 禁用、LuCI、Docker 数据目录和 DNS 链路。
4. 对新镜像使用独立磁盘和测试客户端。备份配置并保留旧启动盘。确认旧盘的 LAN、WAN 和 IPv6 设置后再执行回退。

当前一键准备脚本覆盖官方底座和 Netdata 方案。完整网络界面配置仍按上述步骤组装第三方配方。

## 补丁维护

| 文件 | 作用 |
| --- | --- |
| [Netdata 配置读取](../patches/custom-ipv4/netdata-config-readable.patch) | 让专用服务账号读取配置；应用后包版本为 2.12.3-r2。 |
| [Netdata 容器流量](../patches/custom-ipv4/netdata-container-network.patch) | 同一上游版本补齐 `cgroup-network`、脚本和日志助手；仅采集器获得上游要求的权限；应用后包版本为 2.12.3-r3。 |
| [Netdata LuCI 入口](../patches/custom-ipv4/netdata-luci-bundled-dashboard.patch) | 直接加载本地 `/v3/` 仪表盘。 |
| [LuCI 防火墙状态](../patches/custom-ipv4/luci-nftables-legacy-warning.patch) | 识别 iptables 的 nf_tables 后端，保留真正的 legacy 告警。 |
| [LuCI 文件管理布局](../patches/custom-ipv4/luci-filemanager-layout.patch) | 文件路径栏和表格适应视口。 |
| [Tailscale 文件归属](../patches/custom-ipv4/tailscale-file-ownership.patch) | 由 LuCI 插件提供服务和配置文件，避免重复归属。 |
| [Docker 版本来源](../patches/custom-ipv4/docker-verified-release-revisions.patch) | 对照固定的 Docker、containerd 和 runc 发布提交。 |
| [启动时配置](../packages/network-ui/93-network-ui) | ttyd 绑定回环，启用 WebSocket 源校验等网络界面默认设置。 |

升级前更新来源锁和校验和。先对目标源码执行 `git apply --check`，再构建并比较 manifest 差异。保留前一版 APK、系统盘和路由器配置备份。
