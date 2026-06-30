// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class SqlParser : Parser {
        private const string[] SQL_FILE_SUFFIXES = {"db", "sqlite", "sqlite3"};

        public SqlParser () {
            Object (
                name: "sql",
                ui_name: C_("import-mode", "Database"),
                filetype_name: C_("file-filter", "SQLite Database"),
                file_suffixes: SQL_FILE_SUFFIXES
            );
        }

        public override void init_import_settings (ImportSettings settings) throws ParseError {
            var reader = new DatabaseReader (settings);
            reader.set_default_selection ();

            settings.set_item ("reader", reader);
        }

        public override void append_settings_widgets (ImportSettings settings, Gtk.Box settings_box) throws ParseError {
            if (settings.get_item ("reader") == null) return;

            settings_box.append (new SqlGroup (settings));
        }

        public override ItemList parse (ImportSettings settings, StyleParameters style) throws ParseError {
            var reader = (DatabaseReader) settings.get_item ("reader");
            ItemList items = new ItemList ();
            reader.parse (items, settings, style);
            return items;
        }
    }
}
