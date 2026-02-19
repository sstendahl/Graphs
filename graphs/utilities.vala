// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gdk;
using Gtk;

namespace Graphs {
    namespace Tools {
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
         * Create a catchall filter
         */
        public FileFilter create_all_filter () {
            var all_filter = new FileFilter () { name = _("All Files")};
            all_filter.add_pattern ("*");
            return all_filter;
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
            if (add_all) list_store.append (create_all_filter ());
            return list_store;
        }

        /**
         * Get the friendly path of a file.
         */
        string get_friendly_path (File file) {
            string uri = file.get_uri ();
            Uri parsed;
            try {
                parsed = Uri.parse (uri, UriFlags.NONE);
            } catch (UriError error) {
                return "";
            }

            string path = Uri.unescape_string (parsed.get_path ());
            string host = parsed.get_host ();
            string full_path = Path.build_filename (host + path);
            string filepath = Path.get_dirname (full_path);

            // Check if this is a document portal path and query the real host path from the file itself
            int uid = (int) Posix.getuid ();
            string doc_portal = @"/run/user/$uid/doc/";
            if (filepath.has_prefix (doc_portal)) {
                string fallback = _("Document Portal");

                FileInfo info;
                try {
                    info = file.query_info ("xattr::document-portal.host-path", FileQueryInfoFlags.NONE);
                } catch (Error e) {
                    return fallback;
                }

                string? host_path = info.get_attribute_string ("xattr::document-portal.host-path");
                if (host_path != null) {
                    // Early portal versions added a "\x00" suffix, trim it if present
                    int len = host_path.length;
                    if (len > 4 && host_path.has_suffix ("\\x00")) {
                        host_path = host_path.substring (0, len - 4);
                    }
                    filepath = Path.get_dirname (host_path);
                } else {
                    return fallback;
                }
            }

            // Remove /var from file path and home path for rpm-ostree based distros
            if (filepath.has_prefix ("/var/home")) {
                filepath = filepath.substring (4);
            }
            string home = Environment.get_home_dir ();
            if (filepath.has_prefix (home)) {
                filepath = "~" + filepath.substring (home.length);
                if (filepath == "~") {
                    filepath = "~/";
                }
            }
            return filepath;
        }

        /**
         * Convert an integer to an alphabetic representation.
         * example: 27 -> AA
         *
         * often used in spreadsheets.
         */
        public static string int_to_alpha (int i) {
            StringBuilder result = new StringBuilder ();
            int num = i + 1;
            while (num > 0) {
                int remainder = (num - 1) % 26;
                result.prepend_c ((char) ('A' + remainder));
                num = (num - 1) / 26;
            }
            return result.free_and_steal ();
        }

        /**
         * Convert an alphabetic representation to an integer.
         * example: AA -> 27
         *
         * often used in spreadsheets.
         */
        public static int alpha_to_int (string label) {
            int index = 0;
            for (int i = 0; i < label.length; i++) {
                char c = label[i];
                if (!c.isalpha ()) return -1;
                index = index * 26 + (c.tolower () - 'a' + 1);
            }
            return index - 1;
        }
    }
}
