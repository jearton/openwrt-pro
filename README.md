# OpenWrt x86 定制固件

基于 OpenWrt 25.12.6 x86/64 的 IPv4 路由器定制方案。使用 APK，保留 LuCI、Docker、实时监控和网络管理。默认禁用 IPv6，镜像验收使用独立实验 LAN。DNS 示例采用 AdGuard Home 作为 LAN 客户端的默认 DNS，Technitium 负责本地 DNS 区域。

- [固件方案、定制步骤与升级](docs/firmware.md)
- [额外组件与 LuCI 菜单](docs/components.md) · [定制补丁索引](patches/README.md)
- [日常使用和验收](docs/usage.md)
- [Technitium 与 AdGuard Home 安装](docs/technitium.md)
- [Technitium Compose 配置](containers/technitium/compose.yaml)
- [构建产物摘要与 APK 清单](manifests/README.md)
- [底座和 feeds 锁定版本](sources.lock.json) · [第三方来源](custom-sources.lock.json)

项目代码采用 GPL-3.0-or-later。各上游组件按其原许可证使用。源码锁和示例配置可公开复用，生成的镜像、软件包签名密钥和 DNS 数据在部署环境独立保管。
