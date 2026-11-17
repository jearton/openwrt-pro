import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys

source, staging, extractor = map(Path, sys.argv[1:4])
selected_packages = set(sys.argv[4:])
raw = source / "image.raw"
artifact = source / "image.gz"
release_sha = "90bf15fe530801540c521189184ea94137a1e1b634cca02b04f6c681f07a39df"
with artifact.open("rb") as f:
    assert hashlib.file_digest(f, "sha256").hexdigest() == release_sha

def rootfs(*args, **kw):
    return subprocess.run([str(extractor), "-o", "134479872", *args], check=True, **kw)

package_db = rootfs("-cat", str(raw), "lib/apk/db/installed", capture_output=True).stdout.decode()
packages = {}
for block in package_db.split("\n\n"):
    pairs = [(line[0], line[2:]) for line in block.splitlines() if len(line)>1 and line[1]==":"]
    package = dict(pairs)
    if "P" not in package:
        continue
    directory=""
    files=[]
    for kind, value in pairs:
        if kind=="F":
            directory=value
        elif kind=="R":
            path=PurePosixPath(directory,value)
            assert not path.is_absolute() and ".." not in path.parts
            if not str(path).startswith("lib/apk/packages/"):
                files.append(str(path))
    packages[package["P"]]=(package,files)

expected = {
    "quickstart":"0.13.1-r1",
    "luci-app-quickstart":"0.12.10-r1",
    "luci-i18n-quickstart-zh-cn":"26.216.48241~ff3fc6d",
    "luci-theme-argon":"2.2.12.4-r20260813",
    "luci-app-argon-config":"0.9.2-r20250326",
    "luci-i18n-argon-zh-cn":"26.225.13967~138463c",
    "luci-i18n-argon-config-zh-cn":"26.218.10356~7efc088",
}
if selected_packages:
    unknown = selected_packages - expected.keys()
    if unknown:
        raise SystemExit(f"Unknown iStoreOS packages: {sorted(unknown)}")
    expected = {name: version for name, version in expected.items() if name in selected_packages}
assert all(packages[p][0]["V"]==v for p,v in expected.items())
extract_file=staging/"extract.paths"
metadata={}
for name, version in expected.items():
    package, files=packages[name]
    payload=staging/name/"payload"
    payload.parent.mkdir(parents=True)
    extract_file.write_text("\n".join(files)+"\n")
    rootfs("-no-progress", "-no-xattrs", "-d", str(payload), "-ef", str(extract_file), str(raw), stdout=subprocess.DEVNULL)
    missing = [f for f in files if not ((payload/f).exists() or (payload/f).is_symlink())]
    assert all(f.startswith("etc/uci-defaults/") for f in missing), (name, missing)
    if missing:
        metadata.setdefault("absent_firstboot_scripts", {})[name] = missing
    deps = package["D"].split()
    if name == "luci-theme-argon":
        rootfs("-no-progress", "-no-xattrs", "-d", str(payload), str(raw), "www/luci-static/resources/easepi", stdout=subprocess.DEVNULL)
        icons=payload/"www/luci-static/resources/easepi"
        metadata["theme_support_assets"]={f.relative_to(payload).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(icons.iterdir())}
        assert len(metadata["theme_support_assets"])==4
    if name == "luci-app-argon-config":
        # Only overlay_root() is used by the theme settings UI.
        cfg = payload/"usr/lib/lua/luci/model/cbi/argon-config.lua"
        text = cfg.read_text()
        calls = set(re.findall(r"\bopkg\.\w+", text))
        assert calls == {"opkg.overlay_root"}
        text = text.replace("local opkg = require 'luci.model.ipkg'\n", "")
        text = text.replace("nxfs.statvfs(opkg.overlay_root())", "(nxfs.statvfs('/overlay') or nxfs.statvfs('/'))")
        cfg.write_text(text)
        deps.remove("luci-lib-ipkg")
    if name == "luci-app-quickstart":
        template=payload/"usr/lib/lua/luci/view/quickstart/main.htm"
        assets=payload/"www/luci-static/quickstart"
        sha=hashlib.sha256()
        for asset in sorted(p for p in assets.rglob("*") if p.is_file()):
            sha.update(asset.relative_to(assets).as_posix().encode()+b"\0"+asset.read_bytes())
        ident="istoreos-"+sha.hexdigest()[:16]
        text=template.read_text().replace("v=0.12.10-r1","v="+ident)
        assert text.count("v="+ident)>=2
        template.write_text(text)
        metadata["asset_version"]=ident
    if name == "quickstart":
        config=payload/"etc/config/quickstart"
        config.write_text(config.read_text().rstrip()+"\n\nconfig disabledisplay 'modules'\n\tlist module 'storage'\n\tlist module 'downloadService'\n")
    if name == "luci-app-argon-config":
        config=payload/"etc/config/argon"
        text,count=re.subn(r"(?m)^(\s*option bing_background) '0'$",r"\1 '1'",config.read_text())
        assert count==1
        config.write_text(text)
    up, _, release = version.rpartition("-r")
    if release:
        release_line=f"PKG_RELEASE:={release}"
    else:
        up=version
        release_line="PKG_RELEASE:="
    arch="all" if package["A"]=="noarch" else package["A"]
    assert arch in ("all","x86_64")
    conf = [f for f in files if f in ("etc/config/quickstart","etc/config/argon")]
    conffiles = "\ndefine Package/"+name+"/conffiles\n"+"\n".join("/"+f for f in conf)+"\nendef\n" if conf else ""
    mk = f"""include $(TOPDIR)/rules.mk

PKG_NAME:={name}
PKG_VERSION:={up}
{release_line}
PKGARCH:={arch}
PKG_LICENSE:={package.get("L","")}

include $(INCLUDE_DIR)/package.mk

RSTRIP:=:

define Package/{name}
  SECTION:=luci
  CATEGORY:=LuCI
  TITLE:={name} from the published iStoreOS 25.12.6 x86/64 image
  DEPENDS:={' '.join('+'+d for d in deps)}
  PKGARCH:={arch}
endef
{conffiles}
define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
endef

define Build/Configure
endef

define Build/Compile
endef

define Package/{name}/install
	$(CP) ./payload/. $(1)/
endef

$(eval $(call BuildPackage,{name}))
"""
    (payload.parent/"Makefile").write_text(mk)
metadata.update({"image":"istoreos-25.12.6-2026110611-x86-64-squashfs-combined-efi.img.gz","sha256":release_sha,"source_commit":"111a9805445a88833c40d38b628fa0dfd02060c8","packages":expected})
(staging/"ui-source.json").write_text(json.dumps(metadata,indent=2)+"\n")
