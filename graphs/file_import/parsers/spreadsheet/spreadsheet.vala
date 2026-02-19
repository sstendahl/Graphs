// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;
namespace Graphs {
public errordomain ParseError {
    INVALID_VALUE,
    NO_DATA
}
public class Spreadsheet : Object {

    public static string index_to_label (int index) {
        string result = "";
        int num = index + 1;
        while (num > 0) {
            int remainder = (num - 1) % 26;
            result = ((char) ('A' + remainder)).to_string () + result;
            num = (num - 1) / 26;
        }
        return result;
    }

    public static int label_to_index (string label) {
        int index = 0;
        for (int i = 0; i < label.length; i++) {
            char c = label[i];
            index = index * 26 + (c - 'A' + 1);
        }
        return index - 1;
    }

    public static double[] parse_column_data (string[] raw_cells, out string header, unichar separator = '.') throws ParseError {
        header = "";
        var data = new Array<double> ();
        foreach (string cell in raw_cells) {
            double value;
            if (try_evaluate_string (cell, out value, separator)) {
                data.append_val (value);
            } else if (data.length == 0) {
                header = cell.strip ();
            } else {
                break;
            }
        }
        if (data.length == 0) {
            throw new ParseError.NO_DATA (_("No numeric data found in column."));
        }
        return data.data;
    }
}

    public class SpreadsheetParser : Object {
        private unichar separator;

        public SpreadsheetParser (ImportSettings settings) {
            this.separator = ColumnsSeparator.parse (
                settings.get_string ("separator")
            ).as_unichar ();
        }

        public double[] parse_column (string[] raw_cells, out string header) throws ParseError {
            return Spreadsheet.parse_column_data (raw_cells, out header, separator);
        }
    }
}
