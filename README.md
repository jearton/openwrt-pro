# OpenWrt x86 定制固件

基于 OpenWrt 25.12.6 x86/64 的 IPv4 路由器定制方案。使用 APK，保留 LuCI、Docker、实时监控和网络管理。默认禁用 IPv6，镜像验收使用独立实验 LAN。DNS 示例采用 AdGuard Home 作为 LAN 客户端的默认 DNS，Technitium 负责本地 DNS 区域。

## 功能清单

### OpenWrt 原生功能

| 菜单或入口 | 功能 |
| --- | --- |
| 状态 | 系统与接口概览、路由表、防火墙规则、系统日志和进程 |
| 系统 | 系统设置、账号密码、Dropbear SSH、启动项、计划任务、挂载点、备份恢复、固件升级、重启和 APK 软件包管理 |
| 网络 → 接口 | 有线 WAN/LAN、静态地址、DHCP 客户端、PPPoE、桥接、VLAN 和静态路由 |
| 网络 → DHCP/DNS | dnsmasq 提供 IPv4 DHCP、本地主机名解析、静态租约和 DNS 转发 |
| 网络 → 防火墙 | firewall4 / nftables 分区、NAT、端口转发、流量规则和软件流量卸载 |

原生功能来自 [OpenWrt](https://github.com/openwrt/openwrt) 和 [LuCI](https://github.com/openwrt/luci)。下表所列为本镜像额外集成的功能和对原有界面的定制，其中也包括从官方 feeds 选入的附加包。

### 定制集成

| LuCI 菜单或入口 | 功能 | 开源来源 |
| --- | --- | --- |
| 首页、网络向导、iStore | 仪表盘、网络向导、应用入口 | [Quickstart](https://github.com/istoreos/quickstart)、[iStore](https://github.com/linkease/istore) |
| 登录页、系统 → Argon 主题设置 | 中文主题设置、登录壁纸和菜单样式 | [Argon](https://github.com/jerrykuku/luci-theme-argon) |
| 系统 → 实时监控、状态 → 统计 | CPU、内存、网口、Docker 容器流量和系统历史图表 | [Netdata](https://github.com/netdata/netdata)、[Netdata LuCI 入口](https://github.com/immortalwrt/luci/tree/6dafdfc6a918044f3d4beea816076b6c82c19919/applications/luci-app-netdata)、[collectd](https://github.com/collectd/collectd) |
| 系统 → 终端、Web 管理 | 受限 Web 终端和 uHTTPd 管理 | [ttyd](https://github.com/tsl0922/ttyd)、[LuCI uHTTPd](https://github.com/openwrt/luci/tree/75a306df84a020c57a631ef5b4c02ace56d93387/applications/luci-app-uhttpd) |
| 系统 → 文件管理、文件传输 | 管理和传输路由器文件 | [LuCI File Manager](https://github.com/openwrt/luci/tree/75a306df84a020c57a631ef5b4c02ace56d93387/applications/luci-app-filemanager)、[Lean LuCI](https://github.com/coolsnowwolf/luci/tree/f43c53a60f11f5d635b7127c775e9c04e2be191d) |
| 系统 → 磁盘管理、分区扩容 | 查看本机磁盘和调整分区 | [DiskMan](https://github.com/sbwml/luci-app-diskman)、[PartExp](https://github.com/sirpdboy/luci-app-partexp) |
| 系统维护 | 定时重启、关机、释放内存、自定义命令 | [Lean LuCI](https://github.com/coolsnowwolf/luci/tree/f43c53a60f11f5d635b7127c775e9c04e2be191d)、[PoweroffDevice](https://github.com/sirpdboy/luci-app-poweroffdevice)、[LuCI Commands](https://github.com/openwrt/luci/tree/75a306df84a020c57a631ef5b4c02ace56d93387/applications/luci-app-commands) |
| 服务 → 容器管理 | Docker Engine、Compose、容器与镜像管理 | [Moby](https://github.com/moby/moby)、[Docker Compose](https://github.com/docker/compose)、[Dockerman](https://github.com/openwrt/luci/tree/75a306df84a020c57a631ef5b4c02ace56d93387/applications/luci-app-dockerman) |
| 服务 → AdGuard Home | 客户端 DNS 过滤与按域转发 | [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome) |
| 服务 → OpenClash | Mihomo 代理和规则分流 | [OpenClash](https://github.com/vernesong/OpenClash)、[Mihomo](https://github.com/MetaCubeX/mihomo) |
| 服务 → DDNS-GO | 动态域名更新 | [DDNS-GO](https://github.com/jeessy2/ddns-go)、[LuCI 插件](https://github.com/sirpdboy/luci-app-ddns-go) |
| 服务 → OAF 行为管理 | 应用识别和访问控制 | [OpenAppFilter](https://github.com/destan19/OpenAppFilter) |
| VPN、网络 → 接口 | Tailscale 管理及 WireGuard 接口支持 | [Tailscale](https://github.com/tailscale/tailscale)、[LuCI Tailscale](https://github.com/jearton/luci-app-tailscale)、[WireGuard Tools](https://git.zx2c4.com/wireguard-tools/) |
| 网络 → 负载均衡、定时限速、SQM | 多 WAN 策略、按规则限速、队列管理 | [mwan3 nftables 版本](https://github.com/dl12345/mwan3)、[Lean LuCI](https://github.com/coolsnowwolf/luci/tree/f43c53a60f11f5d635b7127c775e9c04e2be191d)、[EQoS Plus](https://github.com/sirpdboy/luci-app-eqosplus)、[SQM](https://github.com/tohojo/sqm-scripts) |
| 网络 → 流量统计、网速测试、IP/MAC 绑定 | 客户端和接口计量、测速、静态邻居 | [nlbwmon](https://github.com/jow-/nlbwmon)、[vnStat 配方](https://github.com/openwrt/packages/tree/093d551675b1119a06ef224d419905e8d6b2af1a/net/vnstat2)、[网速测试 LuCI](https://github.com/muink/luci-app-netspeedtest)、[iperf3](https://github.com/esnet/iperf)、[LibreSpeed](https://github.com/librespeed/speedtest-go)、[Lean LuCI](https://github.com/coolsnowwolf/luci/tree/f43c53a60f11f5d635b7127c775e9c04e2be191d) |
| 网络 → DHCP/DNS、Macvlan | 定制快捷页面，沿用 OpenWrt 原生配置接口 | [本项目菜单和页面](image-files/network-ui)、[netifd](https://git.openwrt.org/project/netifd.git) |

Technitium 是按需部署的 [Docker 容器](containers/technitium/compose.yaml)，用于本地权威 DNS 区域。安装方式见 [DNS 文档](docs/technitium.md)，源码见 [Technitium DNS Server](https://github.com/TechnitiumSoftware/DnsServer)。镜像包含的具体版本见 [APK 清单](manifests/openwrt-x86-64-generic.manifest)。

### 本项目的补丁和调整

- **Netdata**补上容器网卡采集器和配套脚本，修正配置权限，LuCI 直接加载本地仪表盘。
- **LuCI**修正文件管理器布局和 iptables 后端识别，调整 DHCP/DNS、Macvlan、Docker 和实时监控的菜单入口。
- **启动和首页**默认禁用 IPv6，ttyd 绑定回环并检查 WebSocket 来源，Quickstart 隐藏存储、下载和远程域名卡片。
- **打包和兼容性**调整 Tailscale 配置文件归属、FileTransfer 的 APK 支持、EQoS 的 x86 构建、EQoS Plus 的 Bash 依赖、mwan3 的构建依赖，并固定 Docker、Mihomo、DDNS-GO 和 Go 的构建输入。

对应文件和应用位置见 [定制补丁索引](patches/README.md)。

## 文档和下载

- [固件方案、定制步骤与升级](docs/firmware.md)
- [额外组件与 LuCI 菜单](docs/components.md) · [定制补丁索引](patches/README.md)
- [日常使用和验收](docs/usage.md) · [从 U 盘启动或安装到内置 SSD](docs/physical-install.md)
- [Technitium 与 AdGuard Home 安装](docs/technitium.md)
- [Technitium Compose 配置](containers/technitium/compose.yaml)
- [CI、GitHub Packages 与固件下载](docs/releases.md) · [构建产物摘要与 APK 清单](manifests/README.md)
- [底座和 feeds 锁定版本](sources.lock.json) · [第三方来源](custom-sources.lock.json)

项目代码采用 GPL-3.0-or-later。各上游组件按其原许可证使用。源码锁和示例配置可公开复用，生成的镜像、软件包签名密钥和 DNS 数据在部署环境独立保管。
