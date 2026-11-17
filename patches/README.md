# 定制补丁索引

补丁以相应 OpenWrt 树、LuCI feed 或已引入的插件配方为应用目录。首先查看每个补丁的目标路径，按来源锁准备相同版本，再执行 git apply --check。功能验收见固件文档和菜单清单。

| 组件 | 补丁 |
| --- | --- |
| Netdata | [配置权限](custom-ipv4/netdata-config-readable.patch)、[容器网卡采集](custom-ipv4/netdata-container-network.patch)、[LuCI 本地仪表盘](custom-ipv4/netdata-luci-bundled-dashboard.patch) |
| ttyd | [LAN 监听、接口未就绪时停止监听，以及 root 密码门槛](custom-ipv4/ttyd-lan-login.patch) |
| LuCI | [iptables 后端识别](custom-ipv4/luci-nftables-legacy-warning.patch)、[文件管理样式](custom-ipv4/luci-filemanager-layout.patch) |
| Docker、Tailscale | [Docker 版本合规](custom-ipv4/docker-verified-release-revisions.patch)、[Tailscale 文件归属](custom-ipv4/tailscale-file-ownership.patch) |
| OpenClash、DDNS-GO、Go | [Mihomo 配方](custom-ipv4/openclash-mihomo.Makefile)、[DDNS-GO 版本](custom-ipv4/ddns-go-6.17.8.patch)、[Go 版本](custom-ipv4/golang-1.27.4.patch) |
| 负载均衡、限速 | [mwan3 构建依赖](custom-ipv4/mwan3-build-dependency.patch)、[EQoS x86](custom-ipv4/eqos-x86.patch)、[EQoS Plus Bash](custom-ipv4/eqosplus-bash.patch) |
| 工具 | [Arpbind](custom-ipv4/arpbind-pinned-luci-include.patch)、[Autoreboot](custom-ipv4/autoreboot-pinned-luci-include.patch)、[FileTransfer LuCI](custom-ipv4/filetransfer-pinned-luci-include.patch)、[FileTransfer APK](custom-ipv4/filetransfer-apk.patch)、[Ramfree](custom-ipv4/ramfree-pinned-luci-include.patch) |

[Quickstart r5 补丁](../packages/quickstart-home-r5/quickstart-openwrt.patch) 对应较早的 Quickstart 源码配置。当前网络界面方案的 Quickstart 来源见 [iStoreOS 资产锁](../packages/istoreos-ui-2026110611/ui-source.json)。
