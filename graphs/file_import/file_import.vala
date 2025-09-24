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
        public Application application { get; construct set; }
        public GLib.ListStore file_filters { get; private set; }

        protected signal uint guess_import_mode_request (ImportSettings settings);
        protected signal void init_import_settings_request (ImportSettings settings);
        protected signal Widget append_settings_widgets_request (ImportSettings settings, Box settings_box);
        protected signal string parse_request (Gee.List<Item> itemlist, ImportSettings settings, Data data);

        private GLib.Settings mode_settings;
        private string[] mode_settings_list;
        private Parser[] parsers;
        private StringList parser_names = new StringList (null);

        protected void setup (Parser[] parsers) {
            this.parsers = parsers;
            foreach (Parser parser in parsers) {
                parser_names.append (parser.ui_name);
            }

            mode_settings = application.get_settings_child ("import-params");
            mode_settings_list = mode_settings.settings_schema.list_children ();

            init_file_filters ();
        }

        private void init_file_filters () {
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

        public Widget append_settings_widgets (ImportSettings settings, Box settings_box) {
            return append_settings_widgets_request.emit (settings, settings_box);
        }

        public StringList get_parser_names () {
            return parser_names;
        }

        public ImportSettings get_settings_for_file (File file) {
            var settings = new ImportSettings (file);
            settings.mode = guess_import_mode_request.emit (settings);
            init_import_settings (settings);
            settings.notify["mode"].connect (() => {
                init_import_settings (settings);
            });
            return settings;
        }

        public void set_as_default (ImportSettings settings) {
            string name = parsers[settings.mode].name;
            if (!(name in mode_settings_list)) return;
            settings.set_as_default (mode_settings.get_child (name));
        }

        public void reset (ImportSettings settings) {
            uint guessed_mode = guess_import_mode_request.emit (settings);
            if (guessed_mode == settings.mode) {
                init_import_settings (settings);
            } else {
                settings.mode = guessed_mode; // init happens automatically
            }
        }

        public string parse (Gee.List<Item> itemlist, ImportSettings settings, Data data) {
            return parse_request.emit (itemlist, settings, data);
        }

        private void init_import_settings (ImportSettings settings) {
            settings.mode_name = parser_names.get_string (settings.mode);
            string name = parsers[settings.mode].name;
            if (name in mode_settings_list) {
                settings.load_from_settings (mode_settings.get_child (name));
            }
            init_import_settings_request.emit (settings);
        }
    }

    public class ImportSettings : Object {
        public File file { get; construct set; }
        public uint mode { get; set; }
        public string mode_name { get; set; }

        public signal void value_changed (string key, Variant val);

        private Map<string, Variant> settings = new Gee.HashMap<string, Variant> ();

        public ImportSettings (File file) {
            Object (
                file: file
            );
        }

        public void load_from_settings (GLib.Settings default_settings) {
            foreach (string key in default_settings.settings_schema.list_keys ()) {
                set_value (key, default_settings.get_value (key));
            }
        }

        public void set_as_default (GLib.Settings settings) {
            foreach (string key in settings.settings_schema.list_keys ()) {
                settings.set_value (key, get_value (key));
            }
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
    }
}
