module("luci.controller.eqosplus", package.seeall)
-- Copyright 2022-2023 sirpdboy <herboy2008@gmail.com>
function index()
    if not nixio.fs.access("/etc/config/eqosplus") then return end
    local e = entry({"admin", "network", "eqosplus"}, cbi("eqosplus"), _("Eqosplus"), 5)
    e.dependent=false
    e.acl_depends = { "luci-app-eqosplus" }
    local status = entry({"admin", "control", "eqosplus", "status"}, call("act_status"))
    status.leaf = true
    status.acl_depends = { "luci-app-eqosplus" }

    local legacy = entry({"admin", "control", "eqosplus"}, alias("admin", "network", "eqosplus"))
    legacy.acl_depends = { "luci-app-eqosplus" }
end

function act_status()
    local sys  = require "luci.sys"
    local e = {}
     e.status = sys.call(" busybox ps -w | grep eqosplus | grep -v grep  >/dev/null ") == 0
    luci.http.prepare_content("application/json")
    luci.http.write_json(e)
end
