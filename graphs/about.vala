// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    public void show_about_dialog (Application application) {
        var file = File.new_for_uri ("resource:///se/sjoerd/Graphs/whats_new");
        string release_notes;
        try {
            release_notes = (string) file.load_bytes ().get_data ();
        } catch {
            release_notes = "";
        }

        var dialog = new Adw.AboutDialog () {
            application_name = _("Graphs"),
            application_icon = application.application_id,
            website = Config.HOMEPAGE_URL,
            developer_name = Config.AUTHOR,
            issue_url = Config.ISSUE_URL,
            version = application.version,
            developers = {
                "Sjoerd Stendahl <contact@sjoerd.se>",
                "Christoph Kohnen <christoph.kohnen@disroot.org>"
            },
            designers = {
                "Sjoerd Stendahl <contact@sjoerd.se>",
                "Christoph Kohnen <christoph.kohnen@disroot.org>",
                "Tobias Bernard <tbernard@gnome.org>"
            },
            copyright = "© 2022 – 2024",
            license_type = License.GPL_3_0,
            translator_credits = _("translator-credits"),
            release_notes = release_notes
        };
        dialog.present (application.window);
    }
}
