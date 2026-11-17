'use strict';
'require view';

return view.extend({
	render() {
		return E('div', {}, [E('h2', {}, _("DHCP/DNS")),
			E('ul', {}, [
				E('li', {}, E('a', { href: L.url("admin", "network", "dhcp") }, _("DHCP"))),
				E('li', {}, E('a', { href: L.url("admin", "network", "dns") }, _("DNS"))),
			])
		]);
	},
	handleSave: null,
	handleSaveApply: null,
	handleReset: null
});
