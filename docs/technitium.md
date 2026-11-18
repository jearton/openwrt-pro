# Technitium DNS

OpenWrt 完整镜像内置 Technitium DNS 15.6.2、ASP.NET Core 10.0.15 musl x86/64 运行时、technitium-console 1.4.2 和 Advanced Forwarding 5.2，由 procd 启动。AdGuard Home 和它的 LuCI 菜单作为备用预装，默认停用。

后台和 LuCI 插件统一来自 [luci-app-technitium](https://github.com/jearton/luci-app-technitium)，源码提交固定在 `technitium-luci.lock.json`。通用包首次安装默认停止且关闭开机启动，本固件通过 `93-technitium-dns` 显式开启，并由网络启动后的 `technitium-provision` 一次性服务配置 DNS 分流、租约名转发和 Advanced Forwarding。软件包升级保留既有启停状态和数据。

## 第一次登录

进入 **服务 → Technitium DNS**，确认服务已运行，打开控制台。控制台监听 TCP 5380，使用自己的管理员账户。用户名为 `admin`，通过已受保护的 SSH 管理连接读取 `/etc/technitium/setup-password`。登录后更改密码，删除一次性密码文件。Technitium 配置保存在 `/etc/technitium/data`，位于系统配置备份范围内。

远程管理可以通过受限的 SSH 转发访问路由器的 `127.0.0.1:5380`。控制台仅在可信管理网络使用。防火墙禁止 WAN 访问 DNS 和控制台。

## DNS 和 OpenClash

- 客户端从 dnsmasq 获取 DHCPv4 租约，DNS 指向路由器的 53 端口，由 Technitium 服务。
- Technitium 条件转发 `.lan` 和初始化时所在 /24 LAN 的反向区到 `127.0.0.1:5353`，由 dnsmasq 回答租约、静态主机名和 PTR。
- 公网查询默认走加密上游。自建区域、多个 A 记录、广告拦截列表、白名单和统计在 Technitium 控制台维护。逐条查询日志按需在 Apps 安装 Query Logs (SQLite) 并设置保留期限。
- OpenClash 默认停用，其 53 端口重定向保持关闭。需要 Fake-IP 时，在 Technitium 的 **Advanced Forwarding** 按客户端源 IP 划分组，只将代理白名单客户端需要 Fake-IP 的域名交给 `127.0.0.1:7874`。其他查询继续走真实 IP 上游。两处白名单使用相同的固定租约地址。
- OpenClash 配置、订阅凭证、用户内网区域和设备白名单由管理员配置。

修改 LAN 网段或 DHCP 域后，在控制台同步修改条件转发区和反向区。 路由器重启后，动态租约名称随客户端重新取得租约而恢复。如果 dnsmasq 已能回答该名称，Technitium 仍显示 NXDOMAIN，可在控制台的 Cache 删除对应名称和 PTR 的缓存。切换到备用 AdGuard Home 时，先在备用端口确认应答，再在维护窗口停 Technitium 并让 AdGuard Home 接管 LAN 的 53 端口。

## 从旧镜像升级

先备份旧固件、OpenWrt 配置、AdGuard YAML，以及容器版 Technitium 的数据目录。新镜像首启会配置 LAN 的主 DNS 和 DHCP 辅助端口。升级后在控制台导入自有区域和设置，复核现有 DHCP 选项指向路由器。涉及防火墙、网络和服务启动的改动应先在隔离环境验收。

回退时使用旧镜像及其配置备份，恢复原来的 AdGuard 入口和 Technitium 容器数据。旧方案见 [容器版部署记录](technitium-legacy-docker.md)。
