# 使用与验收

## 管理后台

从独立实验 LAN 打开 LuCI，完成密码设置。可用仅绑定管理机回环的 SSH 转发访问 LuCI 和 Netdata，Mac 用于后台管理。使用隔离客户端验证 DNS、网关和代理的数据面。

- **系统 → 实时监控** 查看主机指标和容器网络流量。
- **服务 → Technitium DNS** 查看服务状态和开机启动设置，打开独立的 DNS 控制台。详见 [DNS 使用文档](technitium.md)。
- **网络 → DHCP/DNS** 管理 dnsmasq 的 DHCP 和租约 DNS。当前由 Technitium 监听主 DNS 53，DHCP 选项 6 下发路由器地址；dnsmasq 在 5353 提供租约名和本地解析。AdGuard Home 为默认停用的备用服务。
- **系统 → 备份与升级** 保存配置和升级。实验环境保留旧启动盘。

## 验收

1. 检查 OpenWrt 启动参数含 `ipv6.disable=1`，实验客户端唯一网卡接实验 LAN，实验桥没有生产网络或物理上联。
2. 用浏览器确认 LuCI 登录、终端和实时图表。客户端发起测试 DNS 查询后，核对原生 Technitium 的客户端统计、响应和路由器接口计数。
3. 用客户端默认 DNS 验证 DHCP、UDP/TCP、权威 SOA、NXDOMAIN、`.lan` 和公网 HTTPS。验证 WAN 无法访问主 DNS 和控制台，LAN 无法直连内部辅助 DNS 端口；控制台按管理访问策略验证。
4. 正常关机再启动路由器，复验 DHCP、原生服务自启和监控。需验证 OpenClash 时，单独在隔离客户端验收直连、代理、分流和 DNS。

完整镜像已通过项目见[2026-11-20 验收记录](acceptance-20261120.md)。后续网络功能、已知 DNSSEC 失败项和恢复结果见[VM 扩展验收](vm-extended-validation-20261120.md)；隔离边界及回滚方案见[扩展验收计划](vm-extended-validation-plan.md)，计划不能作为通过结果。
