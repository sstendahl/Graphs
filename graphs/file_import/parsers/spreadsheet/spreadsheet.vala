// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {

public class SpreadsheetDataParser : Object {
    private string[] x_column;
    private string[] y_column;
    private ColumnsSeparator separator;

    public string x_header { get; private set; default = ""; }
    public string y_header { get; private set; default = ""; }
    private int x_data_start = 0;
    private int y_data_start = 0;

    public SpreadsheetDataParser (ImportSettings settings, string[] x_column, string[] y_column) {
        this.x_column = x_column;
        this.y_column = y_column;
        this.separator = ColumnsSeparator.parse (settings.get_string ("separator"));

        string x_header, y_header;
        int x_start, y_start;

        SpreadsheetUtils.analyze_column (x_column, out x_header, out x_start);
        SpreadsheetUtils.analyze_column (y_column, out y_header, out y_start);

        this.x_header = x_header;
        this.x_data_start = x_start;
        this.y_header = y_header;
        this.y_data_start = y_start;
    }

    public new void get_data (out double[] x_data, out double[] y_data) throws Error {
        x_data = parse_column (x_column, x_data_start);
        y_data = parse_column (y_column, y_data_start);
    }

    private double[] parse_column (string[] column, int start_index) throws Error {
        int count = column.length - start_index;
        if (count <= 0) return new double[0];

        var values = new double[count];
        for (int i = 0; i < count; i++) {
            values[i] = parse_value (column[start_index + i], start_index + i);
        }
        return values;
    }

    private double parse_value (string str, int row) throws Error {
        string normalized = normalize_decimal_separator (str);
        double val;

        if (double.try_parse (normalized, out val)) {
            return val;
        }

        throw new ColumnsParseError.IMPORT_ERROR (
            _("Cannot parse value '%s' on row %d").printf (str, row + 1)
        );
    }

    private string normalize_decimal_separator (string str) {
        string cleaned = str.replace (" ", "");
        string decimal_char = (separator == ColumnsSeparator.COMMA ? "," : ".");
        string thousands_char = decimal_char == "," ? "." : ",";

        cleaned = cleaned.replace (thousands_char, "");

        if (decimal_char == ",") {
            cleaned = cleaned.replace (",", ".");
        }

        return cleaned;
    }
}

public class SpreadsheetUtils : Object {
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

    public static void analyze_column (string[] column, out string header, out int data_start) {
        header = "";
        data_start = 0;
        int last_text_index = -1;

        for (int i = 0; i < column.length; i++) {
            double val;
            string s = column[i].strip ().replace (",", ".");

            if (s.length > 0 && double.try_parse (s, out val)) {
                data_start = i;
                if (last_text_index != -1) {
                    header = column[last_text_index].strip ();
                }
                return;
            } else if (s.length > 0) {
                last_text_index = i;
            }
        }
    }
  }
}
