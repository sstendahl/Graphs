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
    }

    public class DataImporter : Object {
        public Application application { get; construct set; }

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
        }

        public Widget append_settings_widgets (ImportSettings settings, Box settings_box) {
            return append_settings_widgets_request.emit (settings, settings_box);
        }

        public void import_from_files (Window window, File[] files) {
            ImportSettings[] settings_list = new ImportSettings[files.length];
            for (uint i = 0; i < files.length; i++) {
                var settings = new ImportSettings (files[i]);
                settings_list[i] = settings;

                settings.mode = guess_import_mode_request.emit (settings);
                init_import_settings (settings);
                settings.notify["mode"].connect (() => {
                    init_import_settings (settings);
                });
            }

            var dialog = new ImportDialog (this, settings_list);
            dialog.accept.connect (() => {
                Gee.List<Item> itemlist = new LinkedList<Item> ();
                foreach (var settings in settings_list) {
                    string message = parse_request.emit (itemlist, settings, window.data);
                    if (message.length != 0) {
                        window.add_toast_string (message);
                    }
                }
                window.data.add_items_from_list (itemlist);
            });
            dialog.present (window);
        }

        public StringList get_parser_names () {
            return parser_names;
        }

        public void set_as_default (ImportSettings settings) {
            string name = parsers[settings.mode].name;
            if (!(name in mode_settings_list)) return;
            settings.set_as_default (mode_settings.get_child (name));
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

    /**
     * Import dialog
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/dialog.ui")]
    public class ImportDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.NavigationView navigation_view { get; }

        [GtkChild]
        private unowned Adw.NavigationPage file_list_page { get; }

        [GtkChild]
        private unowned Adw.NavigationPage file_settings_page { get; }

        [GtkChild]
        private unowned Adw.ComboRow mode { get; }

        [GtkChild]
        private unowned ListBox file_list { get; }

        [GtkChild]
        private unowned Box file_settings_box { get; }

        [GtkChild]
        private unowned Adw.PreferencesGroup button_group { get; }

        public signal void accept ();

        private DataImporter importer;
        private ImportSettings current_settings;

        public ImportDialog (DataImporter importer, ImportSettings[] settings_list) {
            this.importer = importer;
            mode.set_model (importer.get_parser_names ());
            foreach (var settings in settings_list) {
                string filename = Tools.get_filename (settings.file);
                var row = new ImportFileRow (settings, filename);
                row.activated.connect (() => {
                    file_settings_page.set_title (filename);
                    navigation_view.push (file_settings_page);
                    load_settings (settings);
                });
                file_list.append (row);
            }
        }

        private void load_settings (ImportSettings settings) {
            current_settings = null;
            mode.set_selected (settings.mode);
            current_settings = settings;
            load_mode_settings ();
        }

        private void load_mode_settings () {
            Widget widget;
            while ((widget = file_settings_box.get_last_child ()) != null) {
                file_settings_box.remove (widget);
            }

            importer.append_settings_widgets (current_settings, file_settings_box);
            button_group.set_visible (file_settings_box.get_last_child () != null);
        }

        [GtkCallback]
        private void on_mode () {
            if (current_settings == null) return;
            current_settings.mode = mode.get_selected ();
            load_mode_settings ();
        }

        [GtkCallback]
        private void set_as_default () {
            importer.set_as_default (current_settings);
        }

        [GtkCallback]
        private void on_accept () {
            accept.emit ();
            close ();
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/file-row.ui")]
    public class ImportFileRow : Adw.ActionRow {
        [GtkChild]
        private unowned Label mode { get; }

        public ImportFileRow (ImportSettings settings, string filename) {
            set_title (filename);
            settings.bind_property ("mode_name", mode, "label", BindingFlags.SYNC_CREATE);
        }
    }
}
