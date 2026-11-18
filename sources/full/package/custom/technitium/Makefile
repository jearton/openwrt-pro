# SPDX-License-Identifier: GPL-3.0-or-later

include $(TOPDIR)/rules.mk

PKG_NAME:=technitium
PKG_VERSION:=15.6.2
PKG_RELEASE:=1
PKG_LICENSE:=GPL-3.0-only MIT
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)
PKGARCH:=x86_64
RSTRIP:=:
STRIP:=:

include $(INCLUDE_DIR)/package.mk

DNS_ARCHIVE:=DnsServerPortable-$(PKG_VERSION).tar.gz
RUNTIME_VERSION:=10.0.15
RUNTIME_ARCHIVE:=aspnetcore-runtime-$(RUNTIME_VERSION)-linux-musl-x64.tar.gz
CONSOLE_VERSION:=1.4.2
CONSOLE_ARCHIVE:=technitium-console-$(CONSOLE_VERSION).tar.gz
FORWARDING_ARCHIVE:=AdvancedForwardingApp-v5.2.zip

define Download/technitium-server
  URL:=https://download.technitium.com/dns/archive/$(PKG_VERSION)
  FILE:=$(DNS_ARCHIVE)
  URL_FILE:=DnsServerPortable.tar.gz
  HASH:=51f2d4ebaf156a85035e820afde5e1d428f1920a37d7f0c65203fb1766917e08
endef

define Download/technitium-runtime
  URL:=https://builds.dotnet.microsoft.com/dotnet/aspnetcore/Runtime/$(RUNTIME_VERSION)
  FILE:=$(RUNTIME_ARCHIVE)
  HASH:=ee030f624da2ea347e25a432c8b36cdbc6d0dca002151dd17ba926e50ff6d4b0
endef

define Download/technitium-console
  URL:=https://github.com/byGarcia/technitium-console/releases/download/v$(CONSOLE_VERSION)
  FILE:=$(CONSOLE_ARCHIVE)
  URL_FILE:=technitium-console.tar.gz
  HASH:=bde83282ed4d3767dabc09db1a1efe29c4195b51eb501235cc30bf04045d4810
endef

define Download/technitium-forwarding
  URL:=https://download.technitium.com/dns/apps
  FILE:=$(FORWARDING_ARCHIVE)
  HASH:=cb8680a8a8e6eb7516b23359818e7c3e1db0da37d2872363cb89b24e9047eb3a
endef

define Package/technitium
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Technitium DNS Server with web console
  DEPENDS:=@TARGET_x86_64 +libstdcpp +libgcc +libopenssl +libatomic +zlib +ca-bundle +curl +jsonfilter +dnsmasq-full
  URL:=https://technitium.com/dns/
endef

define Package/technitium/description
  Native DNS resolver, ASP.NET Core runtime, web console, and Advanced Forwarding app.
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)/server $(PKG_BUILD_DIR)/dotnet $(PKG_BUILD_DIR)/console
	tar -xzf $(DL_DIR)/$(DNS_ARCHIVE) -C $(PKG_BUILD_DIR)/server
	tar -xzf $(DL_DIR)/$(RUNTIME_ARCHIVE) -C $(PKG_BUILD_DIR)/dotnet
	tar -xzf $(DL_DIR)/$(CONSOLE_ARCHIVE) -C $(PKG_BUILD_DIR)/console
	test -f $(PKG_BUILD_DIR)/server/DnsServerApp.dll
	test -x $(PKG_BUILD_DIR)/dotnet/dotnet
	# The Alpine build ships a separately loaded optional LTTng tracer.
	rm -f $(PKG_BUILD_DIR)/dotnet/shared/Microsoft.NETCore.App/$(RUNTIME_VERSION)/libcoreclrtraceptprovider.so
	test -f $(PKG_BUILD_DIR)/console/index.html
endef

define Build/Compile
endef

define Package/technitium/install
	$(INSTALL_DIR) $(1)/usr/lib/technitium $(1)/etc/init.d $(1)/lib/upgrade/keep.d
	$(CP) $(PKG_BUILD_DIR)/server $(PKG_BUILD_DIR)/dotnet $(PKG_BUILD_DIR)/console $(1)/usr/lib/technitium/
	# Provide the Alpine libc SONAME within the runtime using OpenWrt's musl.
	ln -s /lib/libc.so $(1)/usr/lib/technitium/dotnet/libc.musl-x86_64.so.1
	$(INSTALL_DATA) $(DL_DIR)/$(FORWARDING_ARCHIVE) $(1)/usr/lib/technitium/
	$(INSTALL_BIN) ./files/run $(1)/usr/lib/technitium/run
	$(INSTALL_BIN) ./files/technitium.init $(1)/etc/init.d/technitium
	$(INSTALL_DATA) ./files/backup-paths $(1)/lib/upgrade/keep.d/technitium
endef

$(eval $(call Download,technitium-server))
$(eval $(call Download,technitium-runtime))
$(eval $(call Download,technitium-console))
$(eval $(call Download,technitium-forwarding))
$(eval $(call BuildPackage,technitium))
