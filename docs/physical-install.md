# 在 x86 物理机安装

本项目发布的 `squashfs-combined-efi.img.gz` 用于支持 64 位 UEFI 启动的 x86 软路由。使用显示器和键盘确认能进入启动菜单，先备份原 OpenWrt 配置和内置盘上的重要数据。首次启动只把一台管理电脑接到软路由 LAN，暂时拔掉原 WAN 和生产 LAN。[OpenWrt x86 安装说明](https://openwrt.org/docs/guide-user/installation/openwrt_x86)

## 在 Mac 制作启动 U 盘

下载 [Release](https://github.com/jearton/openwrt-pro/releases) 或 [GitHub Packages](https://github.com/jearton/openwrt-pro/pkgs/container/openwrt-pro%2Ffirmware) 中同一版本的 EFI 镜像、APK 清单和 SHA256SUMS。在下载目录执行：

```sh
shasum -a 256 -c SHA256SUMS
diskutil list external physical
```

按容量、型号和插拔前后的列表变化识别 U 盘。在下面把两个 `N` 换成同一个磁盘编号，例如确认 U 盘是 `disk4` 时使用 `disk4` 与 `rdisk4`。**写入会覆盖整块目标 U 盘。** 使用整盘编号。

```sh
diskutil info /dev/diskN
sudo -v
diskutil unmountDisk /dev/diskN
set -o pipefail
gzip -dc openwrt-x86-64-generic-squashfs-combined-efi.img.gz |
  sudo dd of=/dev/rdiskN bs=4m
sync
diskutil eject /dev/diskN
```

在 Mac 上，写入过程可按 **Control-T** 查看进度。若系统提示磁盘不可读，选择忽略并继续弹出。

## 从 U 盘试启动

把 U 盘插到软路由。在 UEFI 启动菜单选择标有 **UEFI** 的 U 盘。通用 x86 默认给 `eth0` 分配 LAN，给存在的 `eth1` 分配 WAN。具有专用板型规则的设备使用自己的端口分配，机壳印刷的网口号码由硬件决定。新安装的 LAN 默认 IPv4 地址是 `192.168.1.1/24`。恢复旧配置后按实际接口和地址访问。[默认端口规则](https://github.com/openwrt/openwrt/blob/v25.12.6/package/base-files/files/etc/board.d/99-default_network) · [x86 板型规则](https://github.com/openwrt/openwrt/blob/v25.12.6/target/linux/x86/base-files/etc/board.d/02_network)

在控制台执行 `uci show network`、`ip -br link` 和 `ip -br -4 addr`。把网线逐口插拔，观察哪个 Linux 接口变成 `LOWER_UP`，对照配置确认 LAN 设备。把管理电脑接到 LAN，设置以太网 IPv4 为 DHCP，访问 `http://192.168.1.1`。直连测试时，若确认接的是 LAN 且 DHCP 暂未下发地址，可给电脑临时设置 `192.168.1.2/24`。接 WAN 或未加入 LAN 的端口时需要换到 LAN。要用其它口管理，可先通过 LAN 登录，在「网络 → 接口 → 设备」把所需端口加入 LAN 网桥，同时保留当前可用 LAN 口。设置 root 密码，核对 WAN/LAN 和 IPv6 状态，再按需启用服务。

从 U 盘启动时，系统和配置会留在 U 盘。需要保留原内置盘时，关机后拔掉试用 U 盘即可回到原启动盘。

## 安装到内置 SSD

可以将内置 SSD 拆下接到 Mac，确认型号和容量后按相同方法将镜像写入 SSD。内置盘无法拆卸时，用**单独的 Linux Live U 盘**启动软路由，从另一介质提供已经校验的 OpenWrt 镜像。

在 Linux Live 里用 `lsblk` 识别内置 SSD 和启动 U 盘。选定未挂载的目标整盘后才写入。**这一步会清空该内置盘上的分区和系统。** 下例中的 `/dev/nvme0n1` 仅为示例，核对后替换。

```sh
lsblk -o NAME,PATH,SIZE,MODEL,TRAN,TYPE,MOUNTPOINTS
set -o pipefail
gzip -dc openwrt-x86-64-generic-squashfs-combined-efi.img.gz |
  sudo dd of=/dev/nvme0n1 bs=4M status=progress conv=fsync
sudo sync
```

关机，拔掉 Linux Live U 盘，从内置 SSD 的 UEFI 项启动。先单机复验 LAN 管理、DHCP 和端口映射，再接入原网络。需要 Technitium 时，部署容器及 DNS 转发见 [Technitium 安装文档](technitium.md)。
