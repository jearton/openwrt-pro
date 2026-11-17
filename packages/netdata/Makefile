include $(TOPDIR)/rules.mk

PKG_NAME:=netdata
PKG_VERSION:=2.12.3
PKG_RELEASE:=1
PKG_LICENSE:=GPL-3.0-or-later
PKG_SOURCE:=netdata-x86_64-v$(PKG_VERSION).gz.run
PKG_SOURCE_URL:=https://github.com/netdata/netdata/releases/download/v$(PKG_VERSION)
PKG_HASH:=2b3c1afdf18ef788282108afc95ab8e7884c02cb94991b6f8de6ae49f98bd22c

include $(INCLUDE_DIR)/package.mk

# Strip debug sections only from the upstream static agent.
RSTRIP:=:

define Package/netdata
  SECTION:=admin
  CATEGORY:=Administration
  TITLE:=Netdata real-time monitoring
  URL:=https://github.com/netdata/netdata
  DEPENDS:=@x86_64
  USERID:=netdata:netdata
endef

define Package/netdata/conffiles
/etc/netdata/netdata.conf
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	sh ./extract-asset.sh "$(DL_DIR)/$(PKG_SOURCE)" "$(PKG_BUILD_DIR)"
endef

define Build/Compile
endef

define Package/netdata/install
	$(INSTALL_DIR) $(1)/opt/netdata/bin/srv $(1)/opt/netdata/usr/lib/netdata $(1)/opt/netdata/usr/share/netdata $(1)/opt/netdata/usr/libexec/netdata/plugins.d
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/bin/srv/netdata $(1)/opt/netdata/bin/srv/
	$(TARGET_CROSS)strip --strip-debug $(1)/opt/netdata/bin/srv/netdata
	$(CP) $(PKG_BUILD_DIR)/usr/lib/netdata/conf.d $(1)/opt/netdata/usr/lib/netdata/
	$(CP) $(PKG_BUILD_DIR)/usr/share/netdata/web $(1)/opt/netdata/usr/share/netdata/
	$(INSTALL_DIR) $(1)/etc/netdata $(1)/etc/init.d
	$(INSTALL_CONF) ./files/netdata.conf $(1)/etc/netdata/
	$(INSTALL_BIN) ./files/netdata.init $(1)/etc/init.d/netdata
endef

$(eval $(call BuildPackage,netdata))
