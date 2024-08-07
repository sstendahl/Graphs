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

        public ImportDialog (Application application, string[] modes) {
            this.settings = application.get_settings_child ("import-params");
            this.modes = modes;

            if ("columns" in modes) {
                var coumns_group = new ColumnsGroup (this.settings.get_child ("columns"));
                this.mode_box.append (coumns_group);
            }
            present (application.window);
        }

        [GtkCallback]
        private void on_accept () {
            this.accept.emit ();
            close ();
        }

        [GtkCallback]
        private void on_reset () {
            var dialog = (Adw.AlertDialog) Tools.build_dialog ("reset_to_defaults");
            dialog.set_body (_("Are you sure you want to reset the import settings?"));
            dialog.response.connect ((d, response) => {
                if (response == "reset") {
                    foreach (string mode in this.modes) {
                        Tools.reset_settings (this.settings.get_child (mode));
                    }
                }
            });
            dialog.present (this);
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
            this.custom_delimiter.set_visible (this.delimiter.get_selected () == 6);
        }

        public ColumnsGroup (GLib.Settings settings) {
            Tools.bind_settings_to_widgets (settings, this);
        }
    }
}
