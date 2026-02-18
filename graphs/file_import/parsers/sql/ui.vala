// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * UI Widget for SQL file import
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/sql/main-group.ui")]
    public class SqlGroup : Adw.PreferencesGroup {
        [GtkChild]
        public unowned Adw.ComboRow table_row { get; }
        [GtkChild]
        public unowned Adw.ComboRow column_x { get; }
        [GtkChild]
        public unowned Adw.ComboRow column_y { get; }
        [GtkChild]
        public unowned Gtk.Label no_numeric_warning { get; }

        private DatabaseReader db_reader;
        private ImportSettings settings;
        private bool is_initial_setup = true;

        public SqlGroup (ImportSettings settings) throws IOError {
            this.db_reader = (DatabaseReader) settings.get_item ("db-reader");
            this.settings = settings;

            setup_ui ();
        }

        private void setup_ui () throws IOError {
            string[] tables = db_reader.table_names;
            string table_name = settings.get_string ("table-name");

            // TODO: Use StringList.find () instead of manual loop at GNOME 50 runtime
            var table_model = new StringList (tables);
            table_row.set_model (table_model);
            for (int i = 0; i < tables.length; i++) {
                if (tables[i] == table_name) {
                    table_row.set_selected (i);
                    break;
                }
            }
            update_columns ();
            is_initial_setup = false;
        }

        [GtkCallback]
        private void on_table_changed () {
            if (is_initial_setup) return;
            var selected_item = (StringObject) table_row.get_selected_item ();
            if (selected_item == null) return;

            settings.set_string ("table-name", selected_item.get_string ());
            try {
                update_columns ();
            } catch (IOError e) {
                warning ("Could not update columns: %s", e.message);
            }
        }

        [GtkCallback]
        private void on_columns_changed () {
            if (is_initial_setup) return;
            var selected_x = (StringObject) column_x.get_selected_item ();
            var selected_y = (StringObject) column_y.get_selected_item ();

            if (selected_x == null || selected_y == null) return;
            settings.set_string ("x-column", selected_x.get_string ());
            settings.set_string ("y-column", selected_y.get_string ());
        }

        private void update_columns () throws IOError {
            string x_column = settings.get_string ("x-column");
            string y_column = settings.get_string ("y-column");
            string table_name = settings.get_string ("table-name");
            string[] columns = db_reader.get_numeric_columns (table_name);

            if (columns.length == 0) {
                no_numeric_warning.visible = true;
                column_x.sensitive = false;
                column_y.sensitive = false;
            } else {
                no_numeric_warning.visible = false;
                column_x.sensitive = true;
                column_y.sensitive = true;
            }
            var column_model = new StringList (columns);
            column_x.set_model (column_model);
            column_y.set_model (column_model);
            bool found_x = false;
            bool found_y = false;

            // TODO: Use StringList.find () instead of manual loop at GNOME 50 runtime
            for (int i = 0; i < columns.length; i++) {
                if (columns[i] == x_column) {
                    column_x.set_selected (i);
                    found_x = true;
                }
                if (columns[i] == y_column) {
                    column_y.set_selected (i);
                    found_y = true;
                }
                if (found_x && found_y) {
                    break;
                }
            }
        }
    }
}
