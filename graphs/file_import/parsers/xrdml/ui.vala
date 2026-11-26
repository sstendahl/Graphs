// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/xrdml/main-group.ui")]
    private class XrdmlGroup : Adw.PreferencesGroup {
        // must match the row order in main-group.ui
        private const string[] X_AXIS_OPTIONS = {"scan-axis", "q-space"};
        private const string[] INTENSITY_OPTIONS = {"cps", "counts"};

        [GtkChild]
        private unowned Adw.ExpanderRow scans { get; }
        [GtkChild]
        private unowned Adw.ComboRow x_axis { get; }
        [GtkChild]
        private unowned Adw.ComboRow intensity { get; }

        private ImportSettings settings;
        private Gtk.CheckButton[] scan_checks = {};

        public XrdmlGroup (ImportSettings settings) {
            this.settings = settings;
            var reader = (XrdmlReader) settings.get_item ("reader");
            scans.set_visible (reader.n_scans > 1);
            x_axis.set_visible (reader.has_q);
            intensity.set_visible (reader.has_counting_time);

            bind_row (x_axis, settings, "x-axis", X_AXIS_OPTIONS);
            bind_row (intensity, settings, "intensity", INTENSITY_OPTIONS);

            bool[] selected = (bool[]) settings.get_value ("scans");
            for (int i = 0; i < reader.n_scans; i++) {
                var check = new Gtk.CheckButton () { active = selected[i], valign = Gtk.Align.CENTER };
                check.toggled.connect (save_selection);
                var row = new Adw.ActionRow () {
                    title = reader.get_description (i) ?? _("Scan %d").printf (i + 1),
                    use_markup = false,
                    activatable_widget = check,
                };
                row.add_prefix (check);
                scans.add_row (row);
                scan_checks += check;
            }
            update_subtitle (selected);
        }

        [GtkCallback]
        private void on_select_all () {
            foreach (Gtk.CheckButton check in scan_checks) check.set_active (true);
        }

        [GtkCallback]
        private void on_select_none () {
            foreach (Gtk.CheckButton check in scan_checks) check.set_active (false);
        }

        private void save_selection () {
            var selected = new bool[scan_checks.length];
            for (int i = 0; i < selected.length; i++) selected[i] = scan_checks[i].get_active ();
            settings.set_value ("scans", selected);
            update_subtitle (selected);
        }

        private void update_subtitle (bool[] selected) {
            int n_selected = 0;
            foreach (bool is_selected in selected) {
                if (is_selected) n_selected++;
            }
            scans.set_subtitle (_("%d of %d selected").printf (n_selected, selected.length));
            settings.is_valid = n_selected > 0;
        }

        private static void bind_row (Adw.ComboRow row, ImportSettings settings, string key, string[] options) {
            unowned string current = settings.get_string (key);
            for (int i = 0; i < options.length; i++) {
                if (options[i] == current) row.set_selected (i);
            }
            row.notify["selected"].connect (() => {
                settings.set_string (key, options[row.get_selected ()]);
            });
        }
    }
}
