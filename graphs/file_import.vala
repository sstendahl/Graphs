// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {
    // Work around https://bugzilla.gnome.org/show_bug.cgi?id=683599
    public void add_item_to_list (Item item, Gee.List<Item> list) {
        list.add (item);
    }

    enum ImportMode {
        PROJECT,
        COLUMNS,
        XRDML,
        XRY
    }

    private ImportMode parse_import_mode (string mode) {
        switch (mode) {
            case "project": return ImportMode.PROJECT;
            case "columns": return ImportMode.COLUMNS;
            case "xrdm": return ImportMode.XRDML;
            case "xry": return ImportMode.XRY;
            default: assert_not_reached ();
        }
    }

    private string import_mode_to_string (ImportMode mode) {
        return mode.to_string ()[19:].down ();
    }

    public class DataImporter : Object {
        public Application application { get; construct set; }

        protected signal string guess_import_mode_request (ImportSettings settings);
        protected signal void init_import_settings_request (ImportSettings settings);
        protected signal string import_request (Gee.List<Item> itemlist, ImportSettings settings, Data data);

        private GLib.Settings mode_settings;
        private string[] mode_settings_list;

        public void import_from_files (Window window, File[] files) {
            mode_settings = application.get_settings_child ("import-params");
            mode_settings_list = mode_settings.settings_schema.list_children ();

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

            var dialog = new ImportDialog (settings_list);
            dialog.accept.connect (() => {
                Gee.List<Item> itemlist = new LinkedList<Item> ();
                foreach (var settings in settings_list) {
                    string message = import_request.emit (itemlist, settings, window.data);
                    if (message.length != 0) {
                        window.add_toast_string (message);
                    }
                }
                window.data.add_items_from_list (itemlist);
            });
            dialog.present (window);
        }

        private void init_import_settings (ImportSettings settings) {
            if (settings.mode in mode_settings_list) {
                settings.load_from_settings (mode_settings.get_child (settings.mode));
            }
            init_import_settings_request.emit (settings);
        }
    }

    public class ImportSettings : Object {
        public File file { get; construct set; }
        public string mode { get; set; }

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

        public void set_value (string key, Variant val) {
            settings.@set (key, val);
            value_changed.emit (key, val);
        }

        public void set_string (string key, string val) {
            set_value(key, new Variant.string (val));
        }

        public string get_string (string key) {
            return settings.@get (key).get_string ();
        }

        public void set_int (string key, int val) {
            set_value(key, new Variant.int32 (val));
        }

        public int get_int (string key) {
            return settings.@get (key).get_int32 ();
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

        public signal void accept ();

        private ImportSettings current_settings;

        public ImportDialog (ImportSettings[] settings_list) {
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
            current_settings = settings;
            mode.set_selected (parse_import_mode (settings.mode));
            load_mode_settings ();
        }

        private void load_mode_settings () {
            Widget widget;
            while ((widget = file_settings_box.get_last_child ()) != null) {
                file_settings_box.remove (widget);
            }

            switch (current_settings.mode) {
                case "columns":
                    file_settings_box.append (new ColumnsGroup (current_settings));
                    break;
                default: break;
            }
        }

        [GtkCallback]
        private void on_mode () {
            current_settings.mode = import_mode_to_string ((ImportMode) mode.get_selected ());
            load_mode_settings ();
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
            settings.bind_property ("mode", mode, "label", BindingFlags.SYNC_CREATE);
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import-columns.ui")]
    public class ColumnsGroup : Adw.PreferencesGroup {

        [GtkChild]
        public unowned Adw.ComboRow delimiter { get; }

        [GtkChild]
        public unowned Adw.EntryRow custom_delimiter { get; }

        [GtkChild]
        public unowned Adw.ComboRow separator { get; }

        [GtkChild]
        public unowned Adw.SpinRow column_x { get; }

        [GtkChild]
        public unowned Adw.SpinRow column_y { get; }

        [GtkChild]
        public unowned Adw.SpinRow skip_rows { get; }

        public ColumnsGroup (ImportSettings settings) {
            print("%i", settings.get_int ("column-x"));
            custom_delimiter.set_text (settings.get_string ("custom-delimiter"));
            column_x.set_value (settings.get_int ("column-x"));
            column_x.set_value (settings.get_int ("column-y"));
            column_x.set_value (settings.get_int ("skip-rows"));
        }

        [GtkCallback]
        private void on_delimiter () {
            custom_delimiter.set_visible (delimiter.get_selected () == 6);
        }
    }
}
