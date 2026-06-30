// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class SpreadsheetParser : Parser {
        private const string[] SPREADSHEET_FILE_SUFFIXES = {"ods", "xlsx"};

        public SpreadsheetParser () {
            Object (
                name: "spreadsheet",
                ui_name: C_("import-mode", "Spreadsheet"),
                filetype_name: C_("file-filter", "Spreadsheet"),
                file_suffixes: SPREADSHEET_FILE_SUFFIXES
            );
        }

        public override void init_import_settings (ImportSettings settings) throws ParseError {
            settings.set_item ("reader", new SpreadsheetReader (settings.file));
        }

        public override void append_settings_widgets (ImportSettings settings, Gtk.Box settings_box) throws ParseError {
            if (settings.get_item ("reader") == null) return;

            settings_box.append (new SpreadsheetGroup (settings));
            settings_box.append (new SpreadsheetBox (settings));
        }

        public override ItemList parse (ImportSettings settings, StyleParameters style) throws ParseError {
            var reader = (SpreadsheetReader) settings.get_item ("reader");
            ItemList items = new ItemList ();
            reader.parse (settings, style, items);
            return items;
        }
    }
}
