# 固件发布与下载

GitHub Packages 用 OCI 制品存储 EFI 固件、APK 清单和 SHA-256 校验和。使用 ORAS 下载并核对校验和：

```sh
oras pull ghcr.io/jearton/openwrt-pro/firmware:v25.12.6-20261117
sha256sum -c SHA256SUMS
```

安装或升级前，先在隔离环境复验 EFI 启动、IPv6 禁用、LuCI 和 DNS。保留旧磁盘和配置备份。具体步骤见[固件方案](firmware.md)。

## 持续集成

推送到 main 或创建 PR 后，GitHub Actions 检查清单摘要、Netdata 补丁和 Compose 的回环端口映射。发布工作流下载对应 GitHub Release 的三个文件，用 Git tag 上的清单核对 SHA-256，检测 gzip 完整性，发布为 GHCR 同名版本，再按 OCI 摘要拉回核验。工作流摘要记录可直接使用的摘要引用。

## 发布下一版

1. 按[构建步骤](firmware.md)在 Linux 构建和验收固件。更新 `manifests/` 中的 APK 清单和两个 SHA-256 值，并推送对应 Git 提交。
2. 对该提交创建版本 Git tag。下载名包含小写 `v` 前缀，例如 `v25.12.6-20261117`。
3. 用同名 tag 创建 GitHub Release，将以下三个文件作为 Release 附件上传并发布：
   - `openwrt-x86-64-generic-squashfs-combined-efi.img.gz`
   - `openwrt-x86-64-generic.manifest`
   - `SHA256SUMS`
4. 查看 **Publish firmware to GHCR** 的 Actions 日志。重新发布已存在的 Release 可通过工作流的手动触发入口执行。新的固件内容使用新版本 tag。

完整定制版的构建入口为 **Build full firmware and publish candidate**。该工作流用 GitHub 托管的 Linux x86_64 runner 编译，完整 APK 名称和版本与仓库中的清单逐项比对，生成 `ci-运行编号-尝试次数` 的 GHCR 候选镜像。手动重跑从 Actions 的 workflow_dispatch 入口进入。命名 Release 的发布流程见上文。首次创建的 GitHub Package 默认私有，公开仓库的所有者可在该 Package 的设置里将它切换为 Public。[GitHub Packages 可见性说明](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility#configuring-visibility-of-packages-for-your-personal-account)
