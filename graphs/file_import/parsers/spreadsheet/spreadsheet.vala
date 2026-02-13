// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {

[Compact]
private class SpreadsheetColumn {
    public double[] data;
    public string header = "";
    public uint requests = 0;

    public double[] get_data () {
        if (requests == 0) assert_not_reached ();
        // If this is the last time the data is needed, transfer ownership
        if (requests-- == 1) return (owned) data;
        return data;
    }
}

private class ColumnStrings {
    public string[] data;
    public ColumnStrings (owned string[] data) {
        this.data = (owned) data;
    }
}

public class SpreadsheetDataParser : Object {
    private ArrayList<ColumnStrings> columns_data;
    private ColumnsSeparator separator;

    private SpreadsheetColumn[] parsed_columns;
    private Bitset used_indices = new Bitset.empty ();
    private uint n_used_indices;
    private uint[] index_to_rank;

    public SpreadsheetDataParser (ImportSettings settings) {
        this.columns_data = new ArrayList<ColumnStrings> ();
        this.separator = ColumnsSeparator.parse (settings.get_string ("separator"));

        string[] item_strings = settings.get_string ("items").split (";;");
        ColumnsItemSettings item_settings = ColumnsItemSettings ();

        // Collect used indices
        foreach (string item_string in item_strings) {
            item_settings.load_from_item_string (item_string);

            if (!item_settings.single_column) {
                used_indices.add (item_settings.column_x);
            }
            used_indices.add (item_settings.column_y);
        }
        this.n_used_indices = (uint) used_indices.get_size ();

        // Build index to rank mapping
        uint max_index = 0;
        var bitset_iter = BitsetIter ();
        uint column_index;
        bitset_iter.init_first (used_indices, out column_index);
        do {
            if (column_index > max_index) max_index = column_index;
        } while (bitset_iter.next (out column_index));

        index_to_rank = new uint[max_index + 1];
        uint rank = 0;
        bitset_iter.init_first (used_indices, out column_index);
        do {
            index_to_rank[column_index] = rank++;
        } while (bitset_iter.next (out column_index));

        // Initialize parsed columns
        this.parsed_columns = new SpreadsheetColumn[n_used_indices];
        for (uint i = 0; i < n_used_indices; i++) {
            parsed_columns[i] = new SpreadsheetColumn ();
        }

        // Count requests per column
        foreach (string item_string in item_strings) {
            item_settings.load_from_item_string (item_string);

            if (!item_settings.single_column) {
                uint x_rank = index_to_rank[item_settings.column_x];
                parsed_columns[x_rank].requests++;
            }
            uint y_rank = index_to_rank[item_settings.column_y];
            parsed_columns[y_rank].requests++;
        }
    }

    public void add_column (owned string[] column_data) {
        columns_data.add (new ColumnStrings ((owned) column_data));
    }

    public void parse () throws Error {
        if (columns_data.size != n_used_indices) {
            throw new ColumnsParseError.INDEX_ERROR (
                _("Expected %u columns, got %u").printf ((uint) n_used_indices, columns_data.size)
            );
        }

        var bitset_iter = BitsetIter ();
        uint column_index;
        uint first_column_index = 0;
        uint column_rank = 0;
        int expected_data_start = -1;
        int expected_data_count = -1;

        bitset_iter.init_first (used_indices, out column_index);
        first_column_index = column_index;
        do {
            int data_start;
            int data_count;
            parse_column (columns_data[(int) column_rank].data, column_index, column_rank++, out data_start, out data_count);

            // Validate that all columns have data starting at the same row
            if (expected_data_start == -1) {
                expected_data_start = data_start;
                expected_data_count = data_count;
            } else {
                if (data_start != expected_data_start) {
                    string first_col = SpreadsheetUtils.index_to_label ((int) first_column_index);
                    string curr_col = SpreadsheetUtils.index_to_label ((int) column_index);
                    throw new ColumnsParseError.IMPORT_ERROR (
                        _("Column %s starts at row %d, but column %s starts at row %d. All columns must be aligned.")
                        .printf (first_col, data_start + 1, curr_col, expected_data_start + 1)
                    );
                }
                if (data_count != expected_data_count) {
                    string first_col = SpreadsheetUtils.index_to_label ((int) first_column_index);
                    string curr_col = SpreadsheetUtils.index_to_label ((int) column_index);
                    throw new ColumnsParseError.IMPORT_ERROR (
                        _("Column %s has %d rows, but column %s has %d rows. All columns must have the same length.")
                        .printf (first_col, data_count, curr_col, expected_data_count)
                    );
                }
            }
        } while (bitset_iter.next (out column_index));
    }

    public string get_header (uint index) {
        return parsed_columns[index_to_rank[index]].header;
    }

    public double[] get_column (uint index) {
        return parsed_columns[index_to_rank[index]].get_data ();
    }

    private void parse_column (string[] column, uint column_index, uint column_rank,
                               out int data_start, out int data_count) throws Error {
        parsed_columns[column_rank].data = new double[column.length];
        int value_size = 0;
        data_start = -1;
        for (int i = 0; i < column.length; i++) {
            string expression = column[i].strip ();
            if (expression.length == 0) continue;
            expression = normalize_decimal_separator (expression);
            double val;
            if (try_evaluate_string (expression, out val)) {
                // Record where data actually starts
                if (data_start == -1) {
                    data_start = i;
                }
                parsed_columns[column_rank].data[value_size++] = val;
                continue;
            }
            if (value_size > 0) {
                throw new ColumnsParseError.IMPORT_ERROR (
                    _("Cannot parse value '%s' on row %d").printf (column[i], i + 1)
                );
            }
            parsed_columns[column_rank].header = expression;
        }
        if (value_size == 0) {
            throw new ColumnsParseError.IMPORT_ERROR (
                _("Missing data in column %u").printf (column_index)
            );
        }
        // shrink to actual size
        parsed_columns[column_rank].data.resize (value_size);
        data_count = value_size;
    }

    private string normalize_decimal_separator (string str) {
        // First remove spaces (used as thousands separators in some locales)
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
}
}
