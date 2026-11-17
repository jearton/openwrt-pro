# 使用与验收

## 管理后台

从独立实验 LAN 打开 LuCI，完成密码设置。可用仅绑定管理机回环的 SSH 转发访问 LuCI 和 Netdata，Mac 用于后台管理。使用隔离客户端验证 DNS、网关和代理的数据面。

- **系统 → 实时监控** 查看主机指标和容器网络流量。
- **服务 → 容器管理** 查看 Docker 网络和 DNS 容器。Docker 数据目录放在支持 OverlayFS 的持久文件系统上。
- **网络 → DHCP/DNS** 管理 dnsmasq 的 DHCP 和租约 DNS。AdGuard Home 作为 LAN DNS 时，由 DHCP 选项 6 下发它的 IPv4 地址。
- **系统 → 备份与升级** 保存配置和升级。实验环境保留旧启动盘。

## 验收

1. 检查 OpenWrt 启动参数含 `ipv6.disable=1`，实验客户端唯一网卡接实验 LAN，实验桥没有生产网络或物理上联。
2. 用浏览器确认 LuCI 登录、终端和实时图表。客户端发起测试 DNS 查询后，查看 Technitium 对应容器收发速率。
3. 用客户端默认 DNS 验证 DHCP、UDP/TCP、权威 SOA、NXDOMAIN、`.lan` 和公网 HTTPS。验证客户端无法直连容器 DNS 和管理端口。
4. 正常关机再启动路由器，复验 DHCP、容器重启策略和监控。需验证 OpenClash 时，单独在隔离客户端验收直连、代理、分流和 DNS。
