'use strict';
'require view';
'require uci';

return view.extend({
	load: function() {
		return uci.load('ttyd');
	},

	render: function() {
		const port = uci.get_first('ttyd', 'ttyd', 'port') || '7681';
		if (port === '0')
			return E('div', { class: 'alert-message warning' },
				_('Random ttyd port (port=0) is not supported.<br />Change to a fixed port and try again.'));

		const endpoint = new URL(window.location.origin);
		endpoint.port = port;
		let override;
		if (uci.get_first('ttyd', 'ttyd', 'luci_auth') === '1') {
			endpoint.pathname = '/cgi-bin/luci/terminal-session/';
		} else {
			endpoint.protocol = uci.get_first('ttyd', 'ttyd', 'ssl') === '1' ? 'https:' : 'http:';
			override = uci.get_first('ttyd', 'ttyd', 'url_override');
		}

		const terminal = E('iframe', {
			src: override || endpoint.href,
			title: _('Terminal'),
			style: 'display: block; width: 100%; height: calc(100dvh - 12rem); min-height: 320px; border: none; border-radius: 3px; resize: vertical;'
		});
		const resizeTerminal = () => {
			if (!terminal.isConnected)
				return;
			const top = Math.max(0, terminal.getBoundingClientRect().top);
			terminal.style.height = Math.max(320, window.innerHeight - top - 24) + 'px';
		};
		if (this.resizeTerminal)
			window.removeEventListener('resize', this.resizeTerminal);
		this.resizeTerminal = resizeTerminal;
		window.addEventListener('resize', resizeTerminal, { passive: true });
		terminal.addEventListener('load', resizeTerminal, { once: true });
		window.requestAnimationFrame(resizeTerminal);
		return terminal;
	},

	handleSaveApply: null,
	handleSave: null,
	handleReset: null
});
