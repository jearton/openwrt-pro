# Technitium 与 AdGuard Home

示例使用测试 LAN `192.168.77.0/24`、路由器 `192.168.77.1` 和保留测试域 `lab.test`。部署时使用对应的 LAN 地址和由自己管理的区域。

| 请求 | 处理路径 |
| --- | --- |
| LAN DNS | 客户端 → AdGuard Home `192.168.77.1:53` |
| `lab.test` | AdGuard Home → Technitium `127.0.0.1:1053` |
| `.lan` 和公网 DNS | AdGuard Home → dnsmasq `127.0.0.1:5353` → 原上游，仅公网查询经上游 |
| DHCP | dnsmasq 发放地址，选项 6 指向 `192.168.77.1` |
| 管理入口 | 通过 SSH 本地转发访问路由器上的 `127.0.0.1:5380` 和 `127.0.0.1:3000` |

## 安装 Technitium

OpenWrt 安装 `dockerd`、`docker` 和 `docker-compose`，确认 Docker 运行在支持其存储驱动的持久文件系统上。OpenWrt squashfs 的合并 OverlayFS 目录可能无法解包 whiteout。此时使用独立 ext4 文件系统，或经验证支持 whiteout 的底层持久文件系统。用 `docker info` 检查数据目录及驱动，`docker network inspect bridge` 检查 `EnableIPv6` 为 `false`。

在路由器上放置 [Compose 配置](../containers/technitium/compose.yaml) 后运行以下命令。初始密码文件应归设备管理员所有，只初始化一次。挂载已有数据时，Technitium 沿用已保存的账户和区域。

```sh
cd containers/technitium
umask 077
mkdir -p state secrets
if [ ! -s secrets/admin-password ]; then
    head -c 24 /dev/urandom | od -An -v -tx1 | tr -d ' \n' > secrets/admin-password
fi
chmod 600 secrets/admin-password
docker compose config --quiet
docker compose up -d
docker compose ps
docker port technitium-lab
```

若启用的已是同名容器，先备份其数据目录，将 `TECHNITIUM_CONFIG_DIR` 指向已有目录，再安排短时切换。停止并核对旧容器后删除该容器对象，保留数据目录和原启动定义以供回退。

从管理机建立回环转发，将 `ROUTER` 替换成受控 SSH 地址。登录时使用 `admin` 和本机生成的密码文件内容。

```sh
ssh -NT \
  -L 127.0.0.1:5380:127.0.0.1:5380 \
  -L 127.0.0.1:3000:127.0.0.1:3000 root@ROUTER
```

在 Technitium 的 DNS 设置中将 Local End Points 设为 `0.0.0.0:53`，保留 Recursion 为 Deny，并关闭 IPv6 优先。创建 Primary 区域 `lab.test`，增加 `ns.lab.test` 与 `dns-check.lab.test` 的 A 记录，示例值均为 `192.168.77.1`。在路由器上用 `nslookup -port=1053 dns-check.lab.test 127.0.0.1` 确认应答，再切换客户端 DNS。[Technitium 上游](https://github.com/TechnitiumSoftware/DnsServer)

## 接入 AdGuard Home

安装 `adguardhome`，保留独立管理账户。新部署应在隔离网内初始化账户，再配置最终的回环管理监听。通过 SSH 保留一条管理路径。备份 `/etc/config/dhcp` 和 AdGuard Home 的 YAML，在 AdGuard Home 停止时合并 [示例 DNS 配置](../containers/technitium/adguardhome-dns.example.yaml)，保留既有的用户、过滤规则和 schema 版本。

先用 `AdGuardHome --check-config --config /etc/adguardhome/adguardhome.yaml` 检查配置。检查 5353 和 53 的当前占用。确认 dnsmasq 上游仍是原路由器上游，保留其 DHCP 和当前 `.lan` 域。对 `dhcp.lan.dhcp_option` 先回读，已有其他选项 6 时用当前 LAN 地址替换原值并保留其他选项。

```sh
uci set 'dhcp.@dnsmasq[0].port=5353'
uci add_list 'dhcp.lan.dhcp_option=6,192.168.77.1'
uci commit dhcp
/etc/init.d/dnsmasq restart
/etc/init.d/adguardhome start
```

让隔离客户端续租，用系统 DNS 查询：

```sh
dig dns-check.lab.test A
dig +tcp dns-check.lab.test A
dig lab.test SOA
dig absent-record.lab.test A
dig openwrt.lan A
dig www.cloudflare.com A
dig @192.168.77.1 -p 1053 dns-check.lab.test A +time=1 +tries=1
```

前六个查询均由 `192.168.77.1:53` 应答。其中不存在的区域记录返回 `NXDOMAIN`，并附带该区域 SOA。最后一条直连查询应超时或被拒绝。管理端口同样只允许路由器本机回环访问。切换成功后按部署要求启用 Docker 和 AdGuard Home 开机启动，并在隔离环境里复验一次正常关机和再次启动。[AdGuard Home 条件转发](https://github.com/AdguardTeam/AdGuardHome/wiki/Configuration#specifying-upstreams-for-domains)

## 回退

如果客户端未收到正确 DNS 或原有域名解析失败，先停止 AdGuard Home，恢复备份的 DHCP 配置，重启 dnsmasq，让客户端续租并复测内外网。停用 Technitium 时用 `docker compose down`，保留配置目录。重新部署原容器时使用原启动定义和对应版本的数据备份。
