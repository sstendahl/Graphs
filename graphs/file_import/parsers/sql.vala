// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;
using GLib;
using Sqlite;

namespace Graphs {
    /**
     * Settings object to store selected table and columns
     */
    public class SqlSelection : GLib.Object {
        public string table_name { get; set; }
        public string x_column { get; set; }
        public string y_column { get; set; }

        public SqlSelection (string table, string x_col, string y_col) {
            this.table_name = table;
            this.x_column = x_col;
            this.y_column = y_col;
        }
    }

    /**
     * Database reader class that handles all database operations
     */
    public class DatabaseReader : GLib.Object {
        private Sqlite.Database db;
        private string filename;
        private string[] table_names;

        public DatabaseReader (GLib.File file) throws IOError {
            this.filename = file.get_basename ();
            string file_path = file.get_path ();
            if (Sqlite.Database.open (file_path, out db) != Sqlite.OK) {
                throw new IOError.FAILED (
                    "Failed to open SQL Database: %s".printf (db.errmsg ())
                );
            }
            this.table_names = get_table_names ();
        }

        public string[] get_tables () {
            return this.table_names;
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

        public SqlSelection get_default_selection () throws IOError {
            if (table_names.length == 0) {
                throw new IOError.FAILED ("No tables found in database");
            }

            string first_table = table_names[0];
            string[] columns = get_columns (first_table);

            if (columns.length == 0) {
                throw new IOError.FAILED ("Table has no columns");
            }
            return new SqlSelection (first_table, columns[0], columns[0]);
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

        private DatabaseReader db_reader;
        private SqlSelection selection;

        public SqlGroup (DatabaseReader reader, SqlSelection initial_selection) throws IOError {
            this.db_reader = reader;
            this.selection = initial_selection;
            setup_ui ();
        }

        private void setup_ui () throws IOError {
            string[] tables = db_reader.get_tables ();
            var table_model = new StringList (tables);
            table_row.set_model (table_model);

            for (int i = 0; i < tables.length; i++) {
                if (tables[i] == selection.table_name) {
                    table_row.set_selected (i);
                    break;
                }
            }

            table_row.notify["selected"].connect (on_table_changed);
            column_x.notify["selected"].connect (on_column_changed);
            column_y.notify["selected"].connect (on_column_changed);

            update_columns ();
        }

        private void on_table_changed () {
            var selected_item = table_row.get_selected_item () as StringObject;
            if (selected_item == null) return;

            selection.table_name = selected_item.get_string ();
            try {
                update_columns ();
            } catch (IOError e) {
                warning ("Could not update columns: %s", e.message);
            }
        }

        private void on_column_changed () {
            var x_item = column_x.get_selected_item () as StringObject;
            var y_item = column_y.get_selected_item () as StringObject;

            if (x_item != null) selection.x_column = x_item.get_string ();
            if (y_item != null) selection.y_column = y_item.get_string ();
        }

        private void update_columns () throws IOError {
            string[] columns = db_reader.get_columns (selection.table_name);
            var column_model = new StringList (columns);
            column_x.set_model (column_model);
            column_y.set_model (column_model);

            for (int i = 0; i < columns.length; i++) {
                if (columns[i] == selection.x_column) {
                    column_x.set_selected (i);
                }
                if (columns[i] == selection.y_column) {
                    column_y.set_selected (i);
                }
            }
        }
    }
}
