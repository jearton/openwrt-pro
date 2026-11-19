# x86/64 网络界面镜像

本目录对应 [v25.12.6-20261120](https://github.com/jearton/openwrt-pro/releases/tag/v25.12.6-20261120) 的 189 Linux 构建制品，APK 清单包含 469 个包。固件输入提交为 `c90b0cc20867096a6432462719700c9fd6acbf3e`；后续发布提交补入清单、截图和验收记录。

内置 Technitium 15.6.2-r2、Console 1.4.2、LuCI 插件 1.1.0-r1、Argon 3.1.4、Netdata 2.12.3-r3、ttyd 1.7.7-r6 和 kmod-bonding。AdGuard Home 默认停用，Docker 组件不在镜像内。Netdata、ttyd 和 Technitium 默认自启，IPv6 禁用。

EFI 镜像压缩后为 172805481 字节，SHA256 为：

```text
842079ee87cd5ad0dbdff84d1edf22c09715441adf2177f31ad17fa301520023
```

同一份压缩文件经过 189、PVE 和 Mac 三处校验。全新磁盘在 9000 启动，Mac Chrome 复验登录页、HTTP/HTTPS 终端系统登录与重连、终端高度、实时监控和 Technitium Console。9001 复验 DHCP、A/PTR、公网 DNS、TCP/UDP 53 强制重定向、源 IP 保留、规则关闭/恢复及域名封锁回滚。重启后验证服务自启和 DNS。详见[最终镜像验收记录](../docs/acceptance-20261120.md)。

旧版 v25.12.6-20261118 的 Release 保留原始附件，不替换内容。本次不重新声明 OpenClash 代理分流或物理传感器已经在新镜像上完整验收。
