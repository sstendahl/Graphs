// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;
using Gdk;

namespace Graphs {
    namespace Tools {
        /**
         * Bind settings values to UI.
         */
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
                    var comborow = widget as Adw.ComboRow;
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

        /**
         * Reset a settings instance to default values.
         */
        public void reset_settings (GLib.Settings settings) {
            foreach (string key in settings.settings_schema.list_keys ()) {
                settings.reset (key);
            }
        }

        /**
         * Convert a color in hex representation to Gdk.RGBA
         */
        public Gdk.RGBA hex_to_rgba (string hex) {
            var rgba = Gdk.RGBA ();
            rgba.parse (hex);
            return rgba;
        }

        /**
         * Convert a Gdk.RGBA to a color in hex representation
         */
        public string rgba_to_hex (Gdk.RGBA rgba) {
            var builder = new StringBuilder ("#");
            builder.append ("%02x".printf ((uint)(rgba.red * 255)));
            builder.append ("%02x".printf ((uint)(rgba.green * 255)));
            builder.append ("%02x".printf ((uint)(rgba.blue * 255)));
            return builder.str.up ();
        }

        /**
         * Calculate luminance of a color in hex representation.
         */
        public double get_luminance_from_hex (string hex) {
            return get_luminance_from_rgba (hex_to_rgba (hex));
        }

        private double get_srgb (double color) {
            if (color <= 0.03928) {
                return color / 12.92;
            } else return Math.pow ((color + 0.055) / 1.055, 2.4);
        }

        /**
         * Calculate luminance of a Gdk.RGBA
         */
        public double get_luminance_from_rgba (Gdk.RGBA rgba) {
            double r = get_srgb (rgba.red);
            double g = get_srgb (rgba.green);
            double b = get_srgb (rgba.blue);

            return 0.2126 * r + 0.7152 * g + 0.0722 * b;
        }

        /**
         * Get the contrast between two colors
         */
        public double get_contrast (Gdk.RGBA bg_color, Gdk.RGBA fg_color) {
            double bg_luminance = get_luminance_from_rgba (bg_color);
            double fg_luminance = get_luminance_from_rgba (fg_color);
            double min_value = double.min (bg_luminance, fg_luminance) + 0.05;
            double max_value = double.max (bg_luminance, fg_luminance) + 0.05;
            return max_value / min_value;
        }

        /**
         * Shorten a label
         *
         * @param max_length Maximum length
         */
        public string shorten_label (string label, uint max_length = 20) {
            if (label.length > max_length) {
                return label.substring (0, max_length - 1) + "…";
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

        /**
         * Get the platforms config directory
         */
        public File get_config_directory () throws Error {
            var main_directory = File.new_for_path (Environment.get_user_config_dir ());
            return main_directory.get_child_for_display_name ("graphs");
        }

        /**
         * Get the filename of a file
         */
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

        /**
         * Build a dialog from `dialogs.blp`
         */
        public Object build_dialog (string name) {
            string path = "/se/sjoerd/Graphs/ui/dialogs/" + name.replace ("_", "-") + ".ui";
            var builder = new Builder.from_resource (path);
            return builder.get_object (name + "_dialog");
        }

        /**
         * Open the containing folder of a file
         */
        public void open_file_location (File file) {
            var file_launcher = new FileLauncher (file);
            file_launcher.open_containing_folder.begin (null, null);
        }

        /**
         * Create a file filter matching the suffixes.
         */
        public FileFilter create_file_filter (string name, ...) {
            var file_filter = new FileFilter () { name = name };
            var l = va_list ();
            while (true) {
                string? suffix = l.arg ();
                if (suffix == null) break;
                file_filter.add_suffix (suffix);
            }
            return file_filter;
        }

        /**
         * Create a ListStore with given FileFilters.
         */
        public GLib.ListStore create_file_filters (bool add_all, ...) {
            var list_store = new GLib.ListStore (typeof (FileFilter));
            var l = va_list ();
            while (true) {
                FileFilter? filter = l.arg ();
                if (filter == null) break;
                list_store.append (filter);
            }
            if (add_all) {
                var all_filter = new FileFilter () { name = _("All Files")};
                all_filter.add_pattern ("*");
                list_store.append (all_filter);
            }
            return list_store;
        }
    }
}
