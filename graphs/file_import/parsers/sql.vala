// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;
using GLib;
using Sqlite;

namespace Graphs {
    /**
     * Database reader class that handles all database operations
     */
    public class DatabaseReader : GLib.Object {
        private Sqlite.Database db;
        private string filename;
        private string[] table_names;
        private ImportSettings settings;

        public DatabaseReader (ImportSettings settings) throws IOError {
            this.settings = settings;
            GLib.File file = settings.file;
            this.filename = settings.file.get_basename ();
            string file_path = file.get_path ();
            if (Sqlite.Database.open (file_path, out db) != Sqlite.OK) {
                throw new IOError.FAILED (
                    "Failed to open SQL Database: %s".printf (db.errmsg ())
                );
            }
            this.table_names = get_table_names ();
        }

        public ImportSettings get_settings () {
            return settings;
        }

        public string[] get_tables () {
            return table_names;
        }

        public string[] get_columns (string table_name) throws IOError {
            var columns = new Array<string> ();
            Sqlite.Statement stmt;

            string sql = "PRAGMA table_info(`%s`)".printf (table_name);
            if (db.prepare_v2 (sql, -1, out stmt) != Sqlite.OK) {
                throw new IOError.FAILED (
                    "Failed to retrieve SQL Column names: %s".printf (db.errmsg ())
                );
            }
            while (stmt.step () == Sqlite.ROW) {
                columns.append_val (stmt.column_text (1));
            }
            return columns.data;
        }

        public string[] get_numeric_columns (string table_name) throws IOError {
            var columns = new Array<string> ();
            Sqlite.Statement stmt;

            string sql = "PRAGMA table_info(`%s`)".printf (table_name);
            if (db.prepare_v2 (sql, -1, out stmt) != Sqlite.OK) {
                throw new IOError.FAILED (
                    "Failed to retrieve SQL Column names: %s".printf (db.errmsg ())
                );
            }
            while (stmt.step () == Sqlite.ROW) {
                string col_name = stmt.column_text (1);
                string col_type = stmt.column_text (2).up ();

                // Check if column type is numeric
                if (is_numeric_type (col_type)) {
                    columns.append_val (col_name);
                }
            }
            return columns.data;
        }

        private bool is_numeric_type (string type) {
            return "INT" in type ||
                   "REAL" in type ||
                   "FLOAT" in type ||
                   "DOUBLE" in type ||
                   "NUMERIC" in type ||
                   "DECIMAL" in type;
        }

        public void set_default_selection () throws IOError {
            if (table_names.length == 0) {
                throw new IOError.FAILED ("No tables found in database");
            }

            string first_table = table_names[0];
            string[] columns = get_numeric_columns (first_table);

            settings.set_string ("table_name", first_table);
            if (columns.length == 0) {
                return;
            }
            settings.set_string ("x_column", columns[0]);
            settings.set_string ("y_column", columns[0]);
        }

        public double[] get_column_data (string table_name, string column_name) throws IOError {
            var data = new Array<double> ();
            Sqlite.Statement stmt;
            string sql = "SELECT `%s` FROM `%s`".printf (column_name, table_name);

            if (db.prepare_v2 (sql, -1, out stmt) != Sqlite.OK) {
                throw new IOError.FAILED (
                    "Failed to prepare SQL statement: %s".printf (db.errmsg ())
                );
            }
            while (stmt.step () == Sqlite.ROW) {
                double val = stmt.column_double (0);
                data.append_val (val);
            }

            return data.data;
        }

        private string[] get_table_names () throws IOError {
            var names = new Array<string> ();
            Sqlite.Statement stmt;
            string sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'";
            if (db.prepare_v2 (sql, -1, out stmt) != Sqlite.OK) {
                throw new IOError.FAILED (
                    "Failed to get SQL Table names: %s".printf (db.errmsg ())
                );
            }
            while (stmt.step () == Sqlite.ROW) {
                names.append_val (stmt.column_text (0));
            }
            return names.data;
        }
    }

    /**
     * UI Widget for SQL file import
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/mode-sql.ui")]
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

        public SqlGroup (DatabaseReader reader) throws IOError {
            this.db_reader = reader;
            this.settings = db_reader.get_settings ();
            setup_ui ();
        }

        public string table_name {
            owned get { return settings.get_string ("table_name"); }
            set { settings.set_string ("table_name", value); }
        }
        public string x_column {
            owned get { return settings.get_string ("x_column"); }
            set { settings.set_string ("x_column", value); }
        }
        public string y_column {
            owned get { return settings.get_string ("y_column"); }
            set { settings.set_string ("y_column", value); }
        }

        private void setup_ui () throws IOError {
            string[] tables = db_reader.get_tables ();
            var table_model = new StringList (tables);
            string old = table_name;
            table_row.set_model (table_model);
            table_name = old;
            for (int i = 0; i < tables.length; i++) {
                if (tables[i] == table_name) {
                    table_row.set_selected (i);
                    break;
                }
            }
            update_columns ();
        }

        [GtkCallback]
        private void on_table_changed () {
            var selected_item = table_row.get_selected_item () as StringObject;
            if (selected_item == null) return;
            table_name = selected_item.get_string ();
            try {
                update_columns ();
            } catch (IOError e) {
                warning ("Could not update columns: %s", e.message);
            }
        }

        [GtkCallback]
        private void on_columns_changed () {
            var selected_x = column_x.get_selected_item () as StringObject;
            var selected_y = column_y.get_selected_item () as StringObject;

            if (selected_x == null || selected_y == null) return;
            x_column = selected_x.get_string ();
            y_column = selected_y.get_string ();
        }

        private void update_columns () throws IOError {
            string[] columns = db_reader.get_numeric_columns (table_name);

            if (columns.length == 0) {
                no_numeric_warning.visible = true;
                column_x.sensitive = false;
                column_y.sensitive = false;
            } else {
                no_numeric_warning.visible = false;
                column_x.sensitive = true;
                column_y.sensitive = true;

                var column_model = new StringList (columns);
                string old_x = x_column;
                string old_y = y_column;
                column_x.set_model (column_model);
                column_y.set_model (column_model);
                x_column = old_x;
                y_column = old_y;
                bool found_x = false;
                bool found_y = false;

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
}
