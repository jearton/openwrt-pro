# x86/64 网络界面镜像

此目录对应 [v25.12.6-20261118](https://github.com/jearton/openwrt-pro/releases/tag/v25.12.6-20261118) 的 189 构建制品。APK 清单包含 466 个包。内置 Technitium 15.6.2、LuCI 插件 1.0.0、Netdata 2.12.3-r3 和 `kmod-bonding`。AdGuard Home 默认停用，镜像省去 Docker 组件。

使用本目录的 SHA256SUMS 核对对应 EFI 镜像和 APK 清单。镜像通过静态解包、内核模块 ABI 核验和隔离实验验收。9000 验证了 EFI 启动、原生服务重启自启和浏览器管理，9001 验证了 IPv4 DHCP、设备名解析、DNS 过滤及 OpenClash 白名单分流。
