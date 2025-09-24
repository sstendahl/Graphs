// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/dialog.ui")]
    public class ImportDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.NavigationSplitView navigation_view { get; }

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

        private Window window;
        private DataImporter importer;
        private GLib.ListStore settings_list;
        private ImportSettings current_settings;

        public ImportDialog (Window window, GLib.ListStore settings_list) {
            assert (settings_list.get_item_type () == typeof (ImportSettings));
            this.window = window;
            this.importer = ((Application) window.application).data_importer;
            this.settings_list = settings_list;
            mode.set_model (importer.get_parser_names ());

            file_list.bind_model (settings_list, (item) => {
                return new ImportFileRow ((ImportSettings) item);
            });

            file_list.row_activated.connect (() => {
                if (navigation_view.get_collapsed ()) navigation_view.set_show_content (true);
            });
            file_list.row_selected.connect ((row) => {
                var file_row = (ImportFileRow) row;
                file_settings_page.set_title (file_row.get_title ());
                load_settings (file_row.settings);
            });

            file_list.select_row (file_list.get_row_at_index (0));
            navigation_view.set_show_content (false);

            present (window);
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
        private void on_add () {
            var dialog = new FileDialog ();
            dialog.set_filters (importer.file_filters);
            dialog.open_multiple.begin (window, null, (d, response) => {
                try {
                    var files_list_model = dialog.open_multiple.end (response);
                    for (uint i = 0; i < files_list_model.get_n_items (); i++) {
                        var file = (File) files_list_model.get_item (i);
                        var settings = importer.get_settings_for_file (file);
                        settings_list.append (settings);
                    }
                } catch {}
            });
        }

        [GtkCallback]
        private void on_mode () {
            if (current_settings == null) return;
            current_settings.mode = mode.get_selected ();
            load_mode_settings ();
        }

        [GtkCallback]
        private void on_reset () {
            importer.reset (current_settings);
            load_settings (current_settings);
        }

        [GtkCallback]
        private void set_as_default () {
            importer.set_as_default (current_settings);
        }

        [GtkCallback]
        private void on_accept () {
            Gee.List<Item> itemlist = new LinkedList<Item> ();
            for (uint i = 0; i < settings_list.get_n_items (); i++) {
                var settings = (ImportSettings) settings_list.get_item (i);
                string message = importer.parse (itemlist, settings, window.data);
                if (message.length != 0) {
                    window.add_toast_string (message);
                }
            }
            window.data.add_items_from_list (itemlist);
            close ();
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/file-row.ui")]
    public class ImportFileRow : Adw.ActionRow {
        [GtkChild]
        private unowned Label mode { get; }

        public ImportSettings settings;

        public ImportFileRow (ImportSettings settings) {
            this.settings = settings;
            set_title (Tools.get_filename (settings.file));
            settings.bind_property ("mode_name", mode, "label", BindingFlags.SYNC_CREATE);
        }
    }
}
