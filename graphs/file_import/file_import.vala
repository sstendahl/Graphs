// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {
    // Work around https://bugzilla.gnome.org/show_bug.cgi?id=683599
    public void add_item_to_list (Item item, Gee.List<Item> list) {
        list.add (item);
    }

    public class Parser : Object {
        public string name { get; construct set; }
        public string ui_name { get; construct set; }
        public string filetype_name { get; construct set; }
        public string[] file_suffixes { get; construct set; }
    }

    public class DataImporter : Object {
        public static GLib.ListStore file_filters { get; private set; }

        protected signal uint guess_import_mode_request (ImportSettings settings);
        protected signal bool init_import_settings_request (ImportSettings settings);
        protected signal Widget append_settings_widgets_request (ImportSettings settings, Box settings_box);
        protected signal string parse_request (Gee.List<Item> itemlist, ImportSettings settings, Data data);

        private static GLib.Settings mode_settings;
        private static string[] mode_settings_list;
        private static Parser[] parsers;
        private static StringList parser_names = new StringList (null);

        private static DataImporter instance;

        protected void setup (Parser[] parsers, Application application) {
            DataImporter.parsers = parsers;
            foreach (Parser parser in parsers) {
                parser_names.append (parser.ui_name);
            }

            mode_settings = application.get_settings_child ("import-params");
            mode_settings_list = mode_settings.settings_schema.list_children ();

            init_file_filters ();

            DataImporter.instance = this;
        }

        private static void init_file_filters () {
            file_filters = new GLib.ListStore (typeof (FileFilter));

            var supported_filter = new FileFilter () { name = C_("file-filter", "Supported files") };
            file_filters.append (supported_filter);

            // columns
            var ascii_filter = new FileFilter () { name = C_("file-filter", "ASCII files") };
            string[] ascii_suffixes = {"xy", "dat", "txt", "csv"};
            foreach (string suffix in ascii_suffixes) {
                ascii_filter.add_suffix (suffix);
                supported_filter.add_suffix (suffix);
            }
            file_filters.append (ascii_filter);

            foreach (Parser parser in parsers) {
                if (parser.name == "columns") continue;

                var filter = new FileFilter () { name = parser.filetype_name };
                foreach (string suffix in parser.file_suffixes) {
                    filter.add_suffix (suffix);
                    supported_filter.add_suffix (suffix);
                }
                file_filters.append (filter);
            }

            file_filters.append (Tools.create_all_filter ());
        }

        public static Widget append_settings_widgets (ImportSettings settings, Box settings_box) {
            return instance.append_settings_widgets_request.emit (settings, settings_box);
        }

        public static StringList get_parser_names () {
            return parser_names;
        }

        public static ImportSettings get_settings_for_file (File file) {
            var settings = new ImportSettings (file);
            settings.mode = instance.guess_import_mode_request.emit (settings);
            settings.is_valid = init_import_settings (settings);
            settings.notify["mode"].connect (() => {
                settings.is_valid = init_import_settings (settings);
            });
            return settings;
        }

        public static void set_as_default (ImportSettings settings) {
            string name = parsers[settings.mode].name;
            if (!(name in mode_settings_list)) return;
            settings.set_as_default (mode_settings.get_child (name));
        }

        public static void reset (ImportSettings settings) {
            uint guessed_mode = instance.guess_import_mode_request.emit (settings);
            if (guessed_mode == settings.mode) {
                init_import_settings (settings);
            } else {
                settings.mode = guessed_mode; // init happens automatically
            }
        }

        public static string parse (Gee.List<Item> itemlist, ImportSettings settings, Data data) {
            return instance.parse_request.emit (itemlist, settings, data);
        }

        private static bool init_import_settings (ImportSettings settings) {
            settings.mode_name = parser_names.get_string (settings.mode);
            string name = parsers[settings.mode].name;
            settings.load_from_settings (name in mode_settings_list ? mode_settings.get_child (name) : null);
            return instance.init_import_settings_request.emit (settings);
        }
    }

    public class ImportSettings : Object {
        public File file { get; construct set; }
        public string filename { get; construct set; }
        public uint mode { get; set; }
        public string mode_name { get; set; }
        public bool has_schema { get; private set; default = false; }
        public bool is_valid { get; set; }

        public signal void value_changed (string key, Variant val);

        private Map<string, Variant> settings = new Gee.HashMap<string, Variant> ();
        private Map<string, Object> items = new Gee.HashMap<string, GLib.Object> ();

        public ImportSettings (File file) {
            Object (
                file: file,
                filename: Tools.get_filename (file)
            );
        }

        public void load_from_settings (GLib.Settings? default_settings) {
            if (default_settings == null) {
                has_schema = false;
                return;
            }

            var keys = default_settings.settings_schema.list_keys ();
            has_schema = keys.length > 0;
            foreach (string key in keys) {
                set_value (key, default_settings.get_value (key));
            }
        }

        public void set_as_default (GLib.Settings settings) {
            foreach (string key in settings.settings_schema.list_keys ()) {
                settings.set_value (key, get_value (key));
            }
        }

        public void set_item (string key, GLib.Object item) {
            items.@set (key, item);
        }

        public GLib.Object get_item (string key) {
            return items.@get (key);
        }

        public void set_value (string key, Variant val) {
            settings.@set (key, val);
            value_changed.emit (key, val);
        }

        public Variant get_value (string key) {
            return settings.@get (key);
        }

        public void set_string (string key, string val) {
            set_value (key, new Variant.string (val));
        }

        public string get_string (string key) {
            return get_value (key).get_string ();
        }

        public void set_int (string key, int val) {
            set_value (key, new Variant.int32 (val));
        }

        public int get_int (string key) {
            return get_value (key).get_int32 ();
        }

        public void set_boolean (string key, bool val) {
            set_value (key, new Variant.boolean (val));
        }

        public bool get_boolean (string key) {
            return get_value (key).get_boolean ();
        }
    }
}
