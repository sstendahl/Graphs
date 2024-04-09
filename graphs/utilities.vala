// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;
using Gdk;

namespace Graphs {
    public double min (double a, double b) {
        if (a >= b) {
            return b;
        } else return a;
    }

    public double max (double a, double b) {
        if (a >= b) {
            return a;
        } else return b;
    }

    namespace Tools {
        public void bind_settings_to_widgets (
            GLib.Settings settings, Gtk.Widget parent
        ) {
            foreach (string key in settings.settings_schema.list_keys ()) {
                Gtk.Widget widget;
                parent.get (key, out widget);
                if (widget is Adw.EntryRow) {
                    settings.bind (key, widget, "text", 0);
                }
                else if (widget is Adw.ComboRow) {
                    var comborow = (Adw.ComboRow) widget;
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
            var rgba = Gdk.RGBA ();
            rgba.parse (hex);
            return rgba;
        }

        public string rgba_to_hex (Gdk.RGBA rgba) {
            var builder = new StringBuilder ("#");
            builder.append ("%02x".printf ((uint)(rgba.red * 255)));
            builder.append ("%02x".printf ((uint)(rgba.green * 255)));
            builder.append ("%02x".printf ((uint)(rgba.blue * 255)));
            return builder.str.up ();
        }

        public double get_luminance_from_hex (string hex) {
            return get_luminance_from_rgba (hex_to_rgba (hex));
        }

        private double get_srgb (double color) {
            if (color <= 0.03928) {
                return color / 12.92;
            } else return Math.pow ((color + 0.055) / 1.055, 2.4);
        }


        public double get_luminance_from_rgba (Gdk.RGBA rgba) {
            double r = get_srgb (rgba.red);
            double g = get_srgb (rgba.green);
            double b = get_srgb (rgba.blue);

            return 0.2126 * r + 0.7152 * g + 0.0722 * b;
        }

        public double get_contrast (Gdk.RGBA bg_color, Gdk.RGBA fg_color) {
            double bg_luminance = get_luminance_from_rgba (bg_color);
            double fg_luminance = get_luminance_from_rgba (fg_color);
            double min_value = min (bg_luminance, fg_luminance) + 0.05;
            double max_value = max (bg_luminance, fg_luminance) + 0.05;
            return max_value / min_value;
        }

        public string shorten_label (string label, uint max_length = 20) {
            if (label.length > max_length) {
                return label.substring (0, max_length - 1);
            } else return label;
        }

        public string get_duplicate_string (string original, string[] used) {
            if (!(original in used)) return original;
            string old_str = original;
            try {
                var regex = new Regex ("(?P<string>.+) \\(\\d+\\)");
                MatchInfo info;
                if (regex.match (original, 0, out info)) {
                    old_str = info.fetch_named ("string");
                }
            } catch {}
            uint i = 1;
            while (true) {
                string new_str = @"$old_str ($i)";
                if (!(new_str in used)) return new_str;
                i++;
            }
        }

        public File get_config_directory () throws Error {
            var main_directory = File.new_for_path (Environment.get_user_config_dir ());
            return main_directory.get_child_for_display_name ("graphs");
        }

        public string get_filename (File file) {
            try {
                FileInfo info = file.query_info (
                    "standard::display-name",
                    FileQueryInfoFlags.NONE
                );
                return info.get_display_name ();
            } catch {
                return file.get_basename ();
            }
        }

        public Object build_dialog (string name) {
            var builder = new Builder.from_resource ("/se/sjoerd/Graphs/ui/dialogs.ui");
            return builder.get_object (name);
        }

        public void open_file_location (File file) {
            var file_launcher = new FileLauncher (file);
            file_launcher.open_containing_folder.begin (null, null);
        }
    }
}
