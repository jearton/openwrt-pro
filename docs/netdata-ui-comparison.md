# Netdata 实时监控界面对照

最新实现已升级至 Netdata 2.13.0，保留原生 Dashboard，通过固件内置模板自动初始化每个新浏览器，并设为“实时监控”默认页面。离线、无云账号、独立浏览器和重启验证已通过，见[最终镜像验收](netdata-overview-acceptance-20261120.md)。下表保留此前版本与第三方截图的对照背景。

2026-11-20 核查。用户提供的 Bleach OpenWrt 截图是经典 System Overview 仪表盘，本项目截图是带 Nodes、Metrics、Live、AI Insights 的新版仪表盘。仪表盘主体由 Netdata 的网页资源提供，LuCI 负责嵌入入口；不能仅凭相同的 luci-app 包名认定仪表盘版本相同。

| 项目 | 本项目 | 用户提供的第三方固件 |
| --- | --- | --- |
| 菜单包 | luci-app-netdata，来源为固定的 ImmortalWrt LuCI JS 入口 | [公开插件列表](https://openwrt.mpdn.fun/?dir=%E6%8F%92%E4%BB%B6%E5%88%97%E8%A1%A8)列出 luci-app-netdata |
| 仪表盘 | Netdata 2.12.3 的随包 v3 网页资源 | 截图为经典 System Overview；实际 Agent 版本未验证 |
| 嵌入地址 | 本项目补丁显式改为 http://主机:19999/v3/ | 安装包中的实际地址未验证 |
| 标题 | 本次补丁将页内标题与菜单统一为实时监控，LuCI 包升为 0.1-r1，翻译包升为 0.1 | 截图的页内标题为实时监控 |
| 前端资源 | 当前提取的上游发布资产包含根入口和 v3，没有经典 v1 资源目录 | 截图显示经典前端；不能用页脚的前端构建标识推断 Agent 版本 |

本项目的地址和标题改动见 [Netdata LuCI 补丁](../patches/custom-ipv4/netdata-luci-bundled-dashboard.patch)。这是本项目的定制，目的为直接加载打包在本机的网页资源；没有把新版仪表盘重新绘制成经典界面。现有实验 VM 的 /v1/ 实测返回 404，/v1/index.html 会返回新版入口，不能将换一个 URL 当作经典界面已恢复。

[Netdata 官方说明](https://github.com/netdata/netdata/blob/master/docs/dashboards-and-charts/README.md)区分当前和旧版仪表盘入口。[旧 dashboard 仓库](https://github.com/netdata/dashboard)已归档。因此，界面选择与 Agent 更新应分别评估，不能为了截图外观直接降级采集器，也不能承诺当前固件未打包的经典界面已经可用。

Bleach 作者的[公开仓库](https://github.com/bleach1991/lede)当前主分支提供介绍和来源列表，没有公布该截图对应的 luci-app-netdata 构建提交或安装包。尚未完成第三方安装包的逐文件比对；不能将上游相似实现当作第三方实际交付。

## 网页终端

本项目已发布的 APK 清单中包含官方 luci-app-ttyd，版本 26.288.56989~75a306d。底层另有 ttyd 服务。LuCI 的嵌入脚本调整为复用当前协议、主机和终端会话路径，并填充窗口剩余高度；底层 ttyd 补丁增加 LuCI 会话权限、WebSocket Origin 检查、LAN 限制及证书适配。它们分别是入口和服务，不是另造一个终端应用。

v25.12.6-20261120 已发布清单中的 ttyd 为 1.7.7-r6，包含 Chrome HTTPS/HTTP/2 兼容修复、证书适配及每次系统登录，空密码不放行，已通过该完整镜像的 Mac 浏览器验收。查看物理机实际版本时，以该机的 APK 已安装包查询为准，不能将发布版本当作该机已经安装。

## muink 旧插件与当前入口

[muink/luci-app-netdata](https://github.com/muink/luci-app-netdata)于 2026-01-11 归档。其 [main.js](https://github.com/muink/luci-app-netdata/blob/master/htdocs/luci-static/resources/view/netdata/main.js)也是嵌入 Netdata 网页，并未自行绘制经典 dashboard；它另有启停、端口、SSL、Nginx 及主配置文件编辑页面。当前 ImmortalWrt 入口只嵌入仪表盘，这些管理选项确实存在差异，不能称两套插件功能完全相同。

[ImmortalWrt 主仓库仍提供 JS 入口](https://github.com/immortalwrt/luci/blob/master/applications/luci-app-netdata/htdocs/luci-static/resources/view/netdata.js)，不必因为 muink 仓库归档就重写整个插件。[Netdata 官方界面说明](https://learn.netdata.cloud/docs/dashboards-and-charts/tabs/metrics)也确认新版仍有预置的单节点 CPU、内存、磁盘及网络概览。因此「没有任何预置 dashboard」不准确；当前要解决的是默认呈现方式及软路由常用图表布局。当前打包版本可用的具体默认入口仍须浏览器验证。

2026-11-20 已用 Mac Chrome 的全新浏览器会话只读检查实验机 Netdata 2.12.3 的 /v3/：无需云登录即可看到 CPU、内存、磁盘读写、网络收发预置概览和实时曲线。此检查使用当时已运行的实验机服务，不代表后续新镜像的完整验收已完成，也没有新增或保存自定义 dashboard。
