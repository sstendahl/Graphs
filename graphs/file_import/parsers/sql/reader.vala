// SPDX-License-Identifier: GPL-3.0-or-later
using Sqlite;

namespace Graphs {
    /**
     * Database reader class that handles all database operations
     */
    public class DatabaseReader : GLib.Object {
        private Sqlite.Database db;
        public string[] table_names;
        private ImportSettings settings;

        public DatabaseReader (ImportSettings settings) throws IOError {
            this.settings = settings;
            string file_path = settings.file.get_path ();
            if (Sqlite.Database.open (file_path, out db) != Sqlite.OK) {
                throw new IOError.FAILED (
                    "Failed to open SQL Database: %s".printf (db.errmsg ())
                );
            }
            this.table_names = get_table_names ();
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

            settings.set_string ("table-name", first_table);
            if (columns.length == 0) {
                settings.set_string ("x-column", "");
                settings.set_string ("y-column", "");
                settings.set_string ("xerr-column", "");
                settings.set_string ("yerr-column", "");
            }
            else {
                settings.set_string ("x-column", columns[0]);
                settings.set_string ("y-column", columns[0]);
                settings.set_string ("xerr-column", columns[0]);
                settings.set_string ("yerr-column", columns[0]);
            }
        }

        private double[] get_column_data (string table_name, string column_name) throws IOError {
            double[] result = new double[64];
            int n_results = 0;
            Sqlite.Statement stmt;
            string sql = "SELECT `%s` FROM `%s`".printf (column_name, table_name);

            if (db.prepare_v2 (sql, -1, out stmt) != Sqlite.OK) {
                throw new IOError.FAILED (
                    "Failed to prepare SQL statement: %s".printf (db.errmsg ())
                );
            }

            while (stmt.step () == Sqlite.ROW) {
                if (n_results == result.length) {
                    result.resize (result.length * 2);
                }

                result[n_results++] = stmt.column_double (0);
            }

            result.resize (n_results);

            return result;
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

        public string parse (ItemList items, ImportSettings settings, Data data) throws IOError {
            string table_name = settings.get_string ("table-name");
            if (get_numeric_columns (table_name).length == 0) {
                string msg = _("Could not import data from table \"%s\", no numeric columns were found");
                return msg.printf (table_name);
            }

            string x_column = settings.get_string ("x-column");
            string y_column = settings.get_string ("y-column");
            double[] xdata = get_column_data (table_name, x_column);
            double[] ydata = get_column_data (table_name, y_column);

            if (xdata.length == 0) return _("No data found in table column");

            double[]? xerr = null;
            double[]? yerr = null;
            if (settings.get_boolean ("use-xerr"))
                xerr = get_column_data (table_name, settings.get_string ("xerr-column"));
            if (settings.get_boolean ("use-yerr"))
                yerr = get_column_data (table_name, settings.get_string ("yerr-column"));

            DataItem item = ItemFactory.new_data_item (data, xdata, ydata, xerr, yerr);
            item.xlabel = x_column;
            item.ylabel = y_column;
            item.name = x_column + " vs " + y_column;
            items.add (item);
            return "";
        }
    }
}
