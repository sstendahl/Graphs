// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {
    public errordomain ParseError {
        INVALID,
        INVALID_CONFIGURATION,
        PARSE_ERROR;
    }

    public abstract class Parser : Object {
        public string name { get; construct set; }
        public string ui_name { get; construct set; }
        public string filetype_name { get; construct set; }
        public string[] file_suffixes { get; construct set; }

        public virtual void init_import_settings (ImportSettings settings) throws ParseError {}
        public virtual void append_settings_widgets (ImportSettings settings, Gtk.Box settings_box) throws ParseError {}
        public abstract ItemList parse (ImportSettings settings, StyleParameters style) throws ParseError;
    }

    public class PythonParser : Parser {
        protected signal string init_import_settings_request (ImportSettings settings);
        protected signal string append_settings_widgets_request (ImportSettings settings, Gtk.Box settings_box);
        protected signal string parse_request (ItemList itemlist, ImportSettings settings, StyleParameters style);

        public PythonParser (string name, string ui_name, string filetype_name, string[] file_suffixes) {
            Object (
                name: name,
                ui_name: ui_name,
                filetype_name: filetype_name,
                file_suffixes: file_suffixes
            );
        }

        public override void init_import_settings (ImportSettings settings) throws ParseError {
            string message = init_import_settings_request.emit (settings);
            if (message != "") throw new ParseError.INVALID (message);
        }

        public override void append_settings_widgets (ImportSettings settings, Gtk.Box settings_box) throws ParseError {
            string message = append_settings_widgets_request.emit (settings, settings_box);
            if (message != "") throw new ParseError.INVALID (message);
        }

        public override ItemList parse (ImportSettings settings, StyleParameters style) throws ParseError {
            ItemList items = new ItemList ();
            string message = parse_request.emit (items, settings, style);
            if (message != "") throw new ParseError.INVALID (message);
            return items;
        }
    }

    private const string[] ASCII_SUFFIXES = {"xy", "dat", "txt", "csv"};

    public class DataImporter : Object {
        public static GLib.ListStore file_filters { get; private set; }

        private static GLib.Settings mode_settings;
        private static string[] mode_settings_list;
        private static Parser[] parsers;
        private static StringList parser_names = new StringList (null);

        public DataImporter (Parser[] parsers) {
            DataImporter.parsers = parsers;
            foreach (Parser parser in parsers) {
                parser_names.append (parser.ui_name);
            }

            mode_settings = Application.get_settings_child ("import-params");
            mode_settings_list = mode_settings.settings_schema.list_children ();

            init_file_filters ();
        }

        private static void init_file_filters () {
            file_filters = new GLib.ListStore (typeof (FileFilter));

            var supported_filter = new FileFilter () { name = C_("file-filter", "Supported files") };
            file_filters.append (supported_filter);

            // columns
            var ascii_filter = new FileFilter () { name = C_("file-filter", "ASCII files") };
            foreach (unowned string suffix in ASCII_SUFFIXES) {
                ascii_filter.add_suffix (suffix);
                supported_filter.add_suffix (suffix);
            }
            file_filters.append (ascii_filter);

            foreach (Parser parser in parsers) {
                if (parser.name == "columns") continue;

                var filter = new FileFilter () { name = parser.filetype_name };
                foreach (unowned string suffix in parser.file_suffixes) {
                    filter.add_suffix (suffix);
                    supported_filter.add_suffix (suffix);
                }
                file_filters.append (filter);
            }

            file_filters.append (Tools.create_all_filter ());
        }

        public static void append_settings_widgets (ImportSettings settings, Box settings_box) {
            try {
                parsers[settings.mode].append_settings_widgets (settings, settings_box);
            } catch (ParseError e) {
                settings.is_valid = false;
            }
        }

        public static StringList get_parser_names () {
            return parser_names;
        }

        public static ImportSettings get_settings_for_file (File file) {
            var settings = new ImportSettings (file);
            settings.mode = guess_import_mode (settings);
            settings.is_valid = init_import_settings (settings);
            settings.notify["mode"].connect (() => {
                settings.is_valid = init_import_settings (settings);
            });
            return settings;
        }

        public static void set_as_default (ImportSettings settings) {
            unowned string name = parsers[settings.mode].name;
            if (!(name in mode_settings_list)) return;
            settings.set_as_default (mode_settings.get_child (name));
        }

        public static void reset (ImportSettings settings) {
            uint guessed_mode = guess_import_mode (settings);
            if (guessed_mode == settings.mode) {
                init_import_settings (settings);
            } else {
                settings.mode = guessed_mode; // init happens automatically
            }
        }

        public static ItemList parse (ImportSettings settings, StyleParameters style) throws ParseError {
            return parsers[settings.mode].parse (settings, style);
        }

        private static bool init_import_settings (ImportSettings settings) {
            settings.mode_name = parser_names.get_string (settings.mode);
            unowned string name = parsers[settings.mode].name;
            settings.load_from_settings (name in mode_settings_list ? mode_settings.get_child (name) : null);
            try {
                parsers[settings.mode].init_import_settings (settings);
                return true;
            } catch (ParseError e) {
                return false;
            }
        }

        private static uint guess_import_mode (ImportSettings settings) {
            string filename = Tools.get_filename (settings.file);

            int dot = filename.last_index_of (".");
            if ((dot <= 0 || dot + 1 >= filename.length)) return 0;

            string file_suffix = filename.substring (dot + 1).down ();

            // At index 0 is columns which we use by default
            for (uint index = 1; index < parsers.length; index++) {
                foreach (unowned string suffix in parsers[index].file_suffixes) {
                    if (file_suffix == suffix) return index;
                }
            }

            return 0; // columns
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
            foreach (unowned string key in keys) {
                set_value (key, default_settings.get_value (key));
            }
        }

        public void set_as_default (GLib.Settings settings) {
            foreach (unowned string key in settings.settings_schema.list_keys ()) {
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

        public unowned string get_string (string key) {
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
