include $(TOPDIR)/rules.mk

PKG_NAME:=openclash-mihomo
PKG_VERSION:=1.19.34
PKG_RELEASE:=1
PKG_LICENSE:=GPL-3.0-only
PKG_SOURCE:=mihomo-linux-amd64-v1-v$(PKG_VERSION).gz
PKG_SOURCE_URL:=https://github.com/MetaCubeX/mihomo/releases/download/v$(PKG_VERSION)
PKG_HASH:=0c07340a01408d033dda4088ea2a4c1e4d82aeed7b2f84f7c046e93b6ff3290c

include $(INCLUDE_DIR)/package.mk

define Package/openclash-mihomo
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Mihomo core for OpenClash
  DEPENDS:=@x86_64 +luci-app-openclash
  URL:=https://github.com/MetaCubeX/mihomo
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	gzip -dc $(DL_DIR)/$(PKG_SOURCE) > $(PKG_BUILD_DIR)/clash_meta
endef

define Build/Compile
endef

define Package/openclash-mihomo/install
	$(INSTALL_DIR) $(1)/etc/openclash/core
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/clash_meta $(1)/etc/openclash/core/clash_meta
endef

$(eval $(call BuildPackage,openclash-mihomo))
