// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;
using GLib;
using Sqlite;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/mode-sql.ui")]
    public class SqlGroup : Adw.PreferencesGroup {
        [GtkChild]
        public unowned Adw.ComboRow table_row { get; }
        [GtkChild]
        public unowned Adw.ComboRow column_x { get; }
        [GtkChild]
        public unowned Adw.ComboRow column_y { get; }


        private Sqlite.Database db;
        private string filename;
        private string[] table_names;

        public SqlGroup (GLib.File file) {
            this.filename = file.get_basename ();
            string file_path = file.get_path ();
            if (Sqlite.Database.open (file_path, out db) != Sqlite.OK) {
                return;
            }

            this.table_names = get_table_names ();
            var table_model = new StringList (table_names);
            table_row.set_model (table_model);
            table_row.notify["selected"].connect (update_columns);

            update_columns ();
        }

        private string[] get_table_names () {
            var names = new Array<string> ();
            Sqlite.Statement stmt;

            if (db.prepare_v2 ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
                             -1, out stmt) != Sqlite.OK) {
                return;
            }

            while (stmt.step () == Sqlite.ROW) {
                names.append_val (stmt.column_text (0));
            }

            return names.data;
        }

        private void update_columns () {
            var selected_item = table_row.get_selected_item () as StringObject;
            if (selected_item == null) return;

            string table_name = selected_item.get_string ();
            string[] columns = get_column_names (table_name);

            var column_model = new StringList (columns);
            column_x.set_model (column_model);
            column_y.set_model (column_model);
        }

        private string[] get_column_names (string table_name) {
            var columns = new Array<string> ();
            Sqlite.Statement stmt;

            string sql = "PRAGMA table_info(`%s`)".printf (table_name);
            if (db.prepare_v2 (sql, -1, out stmt) != Sqlite.OK) {
                return;
            }

            while (stmt.step () == Sqlite.ROW) {
                columns.append_val (stmt.column_text (1));
            }

            return columns.data;
        }

        public DataSet? get_selected_data () {
            var table_item = table_row.get_selected_item () as StringObject;
            var x_item = column_x.get_selected_item () as StringObject;
            var y_item = column_y.get_selected_item () as StringObject;

            if (table_item == null || x_item == null || y_item == null) {
                return null;
            }

            string table_name = table_item.get_string ();
            string x_column = x_item.get_string ();
            string y_column = y_item.get_string ();

            return load_data (table_name, x_column, y_column);
        }

        private DataSet? load_data (string table, string x_col, string y_col) {
            var x_data = new Array<double> ();
            var y_data = new Array<double> ();

            Sqlite.Statement stmt;
            string sql = "SELECT `%s`, `%s` FROM `%s`".printf (x_col, y_col, table);

            if (db.prepare_v2 (sql, -1, out stmt) != Sqlite.OK) {
                return null;
            }

            while (stmt.step () == Sqlite.ROW) {
                double x_val = stmt.column_double (0);
                double y_val = stmt.column_double (1);

                x_data.append_val (x_val);
                y_data.append_val (y_val);
            }

            return DataSet () {
                name = this.filename,
                table_name = table,
                x_column_name = x_col,
                y_column_name = y_col,
                xdata = x_data.data,
                ydata = y_data.data
            };
        }
    }

    public struct DataSet {
        public string name;
        public string table_name;
        public string x_column_name;
        public string y_column_name;
        public double[] xdata;
        public double[] ydata;
    }
}
