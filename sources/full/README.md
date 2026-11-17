# 完整定制版配方

这里保存当前完整固件构建所需的插件配方、源码快照和首启设置。来源版本见仓库根目录的 custom-sources.lock.json，OpenWrt 和官方 feeds 的锁定版本见 sources.lock.json。各上游组件沿用自己的许可证。

Netdata 的配方位于 packages/netdata。CI 从固定的 iStoreOS 发布镜像校验并提取 Quickstart 所需资产，再按项目配置统一构建 OpenWrt 镜像。用于 iStore 软件包验签的 PEM 是上游公开验签公钥。
