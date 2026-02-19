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
        private unowned Adw.NavigationPage file_settings_page { get; }

        [GtkChild]
        private unowned Adw.ComboRow mode { get; }

        [GtkChild]
        private unowned ListBox file_list { get; }

        [GtkChild]
        private unowned Box file_settings_box { get; }

        [GtkChild]
        private unowned Adw.PreferencesGroup default_group { get; }

        [GtkChild]
        private unowned Adw.PreferencesGroup remove_group { get; }

        [GtkChild]
        private unowned Button confirm_button { get; }

        private Window window;
        private GLib.ListStore settings_list;
        private ImportSettings current_settings;

        public ImportDialog (Window window, GLib.ListStore settings_list) {
            assert (settings_list.get_item_type () == typeof (ImportSettings));
            this.window = window;
            this.settings_list = settings_list;
            mode.set_model (DataImporter.get_parser_names ());

            file_list.bind_model (settings_list, (item) => {
                ImportSettings settings = (ImportSettings) item;
                if (!settings.is_valid) confirm_button.set_sensitive (false);
                settings.notify["is-valid"].connect (on_is_valid);
                return new ImportFileRow (settings);
            });

            file_list.select_row (file_list.get_row_at_index (0));
            navigation_view.set_show_content (false);

            present (window);
        }

        private void on_is_valid () {
            bool is_valid = true;
            for (uint i = 0; i < settings_list.get_n_items (); i++) {
                ImportSettings settings = (ImportSettings) settings_list.get_item (i);
                is_valid = is_valid && settings.is_valid;
                if (!is_valid) break;
            }
            confirm_button.set_sensitive (is_valid);
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

            DataImporter.append_settings_widgets (current_settings, file_settings_box);
            default_group.set_visible (current_settings.has_schema);
            remove_group.set_visible (settings_list.get_n_items () > 1);
        }

        [GtkCallback]
        private void on_row_activated () {
            if (navigation_view.get_collapsed ()) navigation_view.set_show_content (true);
        }

        [GtkCallback]
        private void on_row_selected (ListBoxRow? row) {
            if (row == null) return;
            var file_row = (ImportFileRow) row;
            file_settings_page.set_title (file_row.settings.filename);
            load_settings (file_row.settings);
        }

        [GtkCallback]
        private void on_add () {
            var dialog = new FileDialog ();
            dialog.set_filters (DataImporter.file_filters);
            dialog.open_multiple.begin (window, null, (d, response) => {
                try {
                    var files_list_model = dialog.open_multiple.end (response);
                    for (uint i = 0; i < files_list_model.get_n_items (); i++) {
                        var file = (File) files_list_model.get_item (i);
                        var settings = DataImporter.get_settings_for_file (file);
                        if (!settings.is_valid) confirm_button.set_sensitive (false);
                        settings_list.append (settings);
                    }
                    remove_group.set_visible (true);
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
            DataImporter.reset (current_settings);
            load_settings (current_settings);
        }

        [GtkCallback]
        private void set_as_default () {
            DataImporter.set_as_default (current_settings);
        }

        [GtkCallback]
        private void remove () {
            uint index;
            settings_list.find (current_settings, out index);
            settings_list.remove (index);
            int new_index = index == 0 ? 0 : (int) index - 1;
            file_list.select_row (file_list.get_row_at_index (new_index));
            on_is_valid ();

            if (navigation_view.get_collapsed ()) navigation_view.set_show_content (false);
        }

        [GtkCallback]
        private void on_accept () {
            Gee.List<Item> itemlist = new LinkedList<Item> ();
            for (uint i = 0; i < settings_list.get_n_items (); i++) {
                var settings = (ImportSettings) settings_list.get_item (i);
                string message = DataImporter.parse (itemlist, settings, window.data);
                if (message.length != 0) {
                    window.add_toast_string (message);
                }
            }
            window.data.add_items_from_list (itemlist);
            close ();
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/file-row.ui")]
    public class ImportFileRow : ListBoxRow {
        [GtkChild]
        private unowned Label filename { get; }

        [GtkChild]
        private unowned Label mode { get; }

        public ImportSettings settings;

        public ImportFileRow (ImportSettings settings) {
            this.settings = settings;
            filename.set_label (settings.filename);
            settings.bind_property ("mode_name", mode, "label", BindingFlags.SYNC_CREATE);
            settings.notify["is-valid"].connect (on_is_valid);
            on_is_valid ();
        }

        private void on_is_valid () {
            if (settings.is_valid) {
                remove_css_class ("error");
            } else {
                add_css_class ("error");
            }
        }
    }
}
