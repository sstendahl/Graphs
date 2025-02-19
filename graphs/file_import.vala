// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Import dialog
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import.ui")]
    public class ImportDialog : Adw.Dialog {

        [GtkChild]
        private unowned Box mode_box { get; }

        private GLib.Settings settings;
        private string[] modes;

        public signal void accept ();

        public ImportDialog (Window window, string[] modes) {
            var application = window.application as Application;
            this.settings = application.get_settings_child ("import-params");
            this.modes = modes;
            if ("columns" in modes) {
                var columns_group = new ColumnsGroup (settings.get_child ("columns"));
                mode_box.append (columns_group);
            }
            if ("sql" in modes) {
                var sql_group = new SqlGroup (settings.get_child ("columns"));
                mode_box.append (sql_group);
            }
            present (window);
        }

        [GtkCallback]
        private void on_accept () {
            accept.emit ();
            close ();
        }

        [GtkCallback]
        private void on_reset () {
            var dialog = Tools.build_dialog ("reset_to_defaults") as Adw.AlertDialog;
            dialog.response.connect ((d, response) => {
                if (response == "reset") {
                    foreach (string mode in modes) {
                        Tools.reset_settings (settings.get_child (mode));
                    }
                }
            });
            dialog.present (this);
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import-sql.ui")]
    public class SqlGroup : Adw.PreferencesGroup {
        public SqlGroup (GLib.Settings settings) {
            Tools.bind_settings_to_widgets (settings, this);
        }
    }


    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import-columns.ui")]
    public class ColumnsGroup : Adw.PreferencesGroup {

        [GtkChild]
        public unowned Adw.ComboRow delimiter { get; }

        [GtkChild]
        public unowned Adw.EntryRow custom_delimiter { get; }

        [GtkChild]
        public unowned Adw.ComboRow separator { get; }

        [GtkChild]
        public unowned Adw.SpinRow column_x { get; }

        [GtkChild]
        public unowned Adw.SpinRow column_y { get; }

        [GtkChild]
        public unowned Adw.SpinRow skip_rows { get; }

        [GtkCallback]
        private void on_delimiter () {
            custom_delimiter.set_visible (delimiter.get_selected () == 6);
        }

        public ColumnsGroup (GLib.Settings settings) {
            Tools.bind_settings_to_widgets (settings, this);
        }
    }
}
