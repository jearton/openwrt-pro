'use strict';
'require view';

return view.extend({
	render() {
		return E('div', {}, [E('h2', {}, _("Macvlan")),
			E('p', {}, _('Open Interfaces, choose Devices, then add a MAC VLAN device.')),
			E('ul', {}, [
				E('li', {}, E('a', { href: L.url("admin", "network", "network") }, _("Network Interfaces"))),
			])
		]);
	},
	handleSave: null,
	handleSaveApply: null,
	handleReset: null
});
