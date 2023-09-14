// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;

namespace Graphs {
    namespace Tools {
        public void bind_settings_to_widgets (
            GLib.Settings settings, Gtk.Window window, string prefix = "",
            string[] ignorelist = {}
        ) {
            foreach (string key in settings.settings_schema.list_keys ()) {
                if (key in ignorelist) {
                    continue;
                }
                Gtk.Widget widget;
                window.get (prefix + key, out widget);
                if (widget is Adw.EntryRow) {
                    settings.bind (key, widget, "text", 0);
                }
                else if (widget is Adw.ComboRow) {
                    Adw.ComboRow comborow = (Adw.ComboRow) widget;
                    comborow.set_selected (settings.get_enum (key));
                    comborow.notify["selected"].connect (() => {
                        if (settings.get_enum (key)
                            != comborow.get_selected ()) {
                            settings.set_enum (
                                key, (int) comborow.get_selected ()
                            );
                        }
                    });
                    settings.changed[key].connect (() => {
                        comborow.set_selected (settings.get_enum (key));
                    });
                }
                else if (widget is Gtk.SpinButton) {
                    settings.bind (key, widget, "value", 0);
                }
                else if (widget is Gtk.Switch) {
                    settings.bind (key, widget, "active", 0);
                }
                else if (widget is Adw.ExpanderRow) {
                    settings.bind (key, widget, "enable-expansion", 0);
                    widget.set_expanded (true);
                }
            }
        }
    }
}
