// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/xrdml/main-group.ui")]
    private class XrdmlGroup : Adw.PreferencesGroup {
        // must match the row order in main-group.ui
        private const string[] X_AXIS_OPTIONS = {"scan-axis", "q-space"};
        private const string[] INTENSITY_OPTIONS = {"cps", "counts"};

        [GtkChild]
        private unowned Adw.ComboRow scan { get; }
        [GtkChild]
        private unowned Adw.ComboRow x_axis { get; }
        [GtkChild]
        private unowned Adw.ComboRow intensity { get; }

        public XrdmlGroup (ImportSettings settings) {
            var reader = (XrdmlReader) settings.get_item ("reader");
            scan.set_visible (reader.n_scans > 1);
            x_axis.set_visible (reader.has_q);
            intensity.set_visible (reader.has_counting_time);

            bind_row (x_axis, settings, "x-axis", X_AXIS_OPTIONS);
            bind_row (intensity, settings, "intensity", INTENSITY_OPTIONS);

            var scans = new Gtk.StringList ({_("All Scans")});
            for (int i = 1; i <= reader.n_scans; i++) {
                scans.append (_("Scan %d").printf (i));
            }
            scan.set_model (scans);
            scan.set_selected (settings.get_int ("scan") + 1);
            scan.notify["selected"].connect (() => {
                settings.set_int ("scan", (int) scan.get_selected () - 1);
            });
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
