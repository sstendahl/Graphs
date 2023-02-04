# SPDX-License-Identifier: GPL-3.0-or-later
languages = fs.read('LINGUAS').strip().split('\n')
i18n.gettext(
	'graphs',
	install_dir: localedir,
	preset: 'glib',
	args: '--from-code=UTF-8',
	languages: languages
)