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

            var builder = new Builder ();
            foreach (string mode in modes) {
                try {
                    builder.add_from_resource (@"/se/sjoerd/Graphs/ui/import-$mode.ui");
                } catch {
                    assert_not_reached ();
                }
                var group = (PreferencesGroup) builder.get_object (mode + "_group");
                GLib.Settings mode_settings = this.settings.get_child (mode);
                foreach (string key in mode_settings.settings_schema.list_keys ()) {
                    Object object = builder.get_object (mode + "_" + key.replace ("-", "_"));
                    bind_setting (mode_settings, object, key);
                }
                // mode specific setups:
                switch (mode) {
                    case "columns": {
                        var delimiter = (Adw.ComboRow) builder.get_object ("columns_delimiter");
                        var custom_delimiter = (Adw.EntryRow) builder.get_object ("columns_custom_delimiter");
                        delimiter.notify["selected"].connect (() => {
                            custom_delimiter.set_visible (delimiter.get_selected () == 6);
                        });
                        break;
                    }
                    default: {
                        break;
                    }
                }
                this.mode_box.append (group);
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

        private static void bind_setting (GLib.Settings settings, Object object, string key) {
            if (object is Adw.EntryRow) {
                settings.bind (key, object, "text", 0);
            }
            else if (object is Adw.ComboRow) {
                var comborow = (Adw.ComboRow) object;
                comborow.set_selected (settings.get_enum (key));
                comborow.notify["selected"].connect (() => {
                    if (settings.get_enum (key) != comborow.get_selected ()) {
                        settings.set_enum (
                            key, (int) comborow.get_selected ()
                        );
                    }
                });
                settings.changed[key].connect (() => {
                    comborow.set_selected (settings.get_enum (key));
                });
            }
            else if (object is Adw.SpinRow) {
                settings.bind (key, object, "value", 0);
            }
        }
    }
}
