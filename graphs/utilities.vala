// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;
using Gdk;

namespace Graphs {
    namespace Tools {
        public void bind_settings_to_widgets (
            GLib.Settings settings, Gtk.Widget parent, string prefix = "",
            string[] ignorelist = {}
        ) {
            foreach (string key in settings.settings_schema.list_keys ()) {
                if (key in ignorelist) {
                    continue;
                }
                Gtk.Widget widget;
                parent.get (prefix + key, out widget);
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
                else if (widget is Gtk.Switch) {
                    settings.bind (key, widget, "active", 0);
                }
                else if (widget is Adw.SwitchRow) {
                    settings.bind (key, widget, "active", 0);
                }
                else if (widget is Adw.ExpanderRow) {
                    settings.bind (key, widget, "enable-expansion", 0);
                    widget.set_expanded (true);
                }
                else if (widget is Adw.SpinRow) {
                    settings.bind (key, widget, "value", 0);
                }
            }
        }

        public void reset_settings (GLib.Settings settings) {
            foreach (string key in settings.settings_schema.list_keys ()) {
                settings.reset (key);
            }
        }

        public Gdk.RGBA hex_to_rgba (string hex) {
            Gdk.RGBA rgba = Gdk.RGBA ();
            rgba.parse (hex);
            return rgba;
        }

        public string rgba_to_hex (Gdk.RGBA rgba) {
            StringBuilder builder = new StringBuilder ("#");
            builder.append ("%02x".printf ((uint)(rgba.red * 255)));
            builder.append ("%02x".printf ((uint)(rgba.green * 255)));
            builder.append ("%02x".printf ((uint)(rgba.blue * 255)));
            return builder.str.up ();
        }

        public double get_luminance_from_hex (string hex) {
            return get_luminance_from_rgba (hex_to_rgba (hex));
        }

        public double get_luminance_from_rgba (Gdk.RGBA rgba) {
            double red_factor = rgba.red * 255 * 0.2126;
            double green_factor = rgba.green * 255 * 0.7152;
            double blue_factor = rgba.blue * 255 * 0.0722;
            return red_factor + green_factor + blue_factor;
        }
    }
}
