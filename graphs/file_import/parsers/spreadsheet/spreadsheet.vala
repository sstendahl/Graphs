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
        if (requests-- == 1) return (owned) data;
        return data;
    }
}

public class SpreadsheetDataParser : Object {
    private SpreadsheetColumn[] parsed_columns;
    private Bitset used_indices = new Bitset.empty ();
    private uint n_used_indices;
    private uint[] index_to_rank;
    private uint columns_added = 0;

    public SpreadsheetDataParser (ImportSettings settings) {
        string[] item_strings = settings.get_string ("items").split (";;");
        ColumnsItemSettings item_settings = ColumnsItemSettings ();

        foreach (string item_string in item_strings) {
            item_settings.load_from_item_string (item_string);
            if (!item_settings.single_column) {
                used_indices.add (item_settings.column_x);
            }
            used_indices.add (item_settings.column_y);
        }

        this.n_used_indices = (uint) used_indices.get_size ();
        if (n_used_indices == 0) return;

        uint max_index = used_indices.get_maximum ();
        index_to_rank = new uint[max_index + 1];

        uint rank = 0;
        var bitset_iter = BitsetIter ();
        uint column_index;

        if (bitset_iter.init_first (used_indices, out column_index)) {
            do {
                index_to_rank[column_index] = rank++;
            } while (bitset_iter.next (out column_index));
        }

        this.parsed_columns = new SpreadsheetColumn[n_used_indices];
        for (uint i = 0; i < n_used_indices; i++) {
            parsed_columns[i] = new SpreadsheetColumn ();
        }

        foreach (string item_string in item_strings) {
            item_settings.load_from_item_string (item_string);
            if (!item_settings.single_column) {
                parsed_columns[index_to_rank[item_settings.column_x]].requests++;
            }
            parsed_columns[index_to_rank[item_settings.column_y]].requests++;
        }
    }

    public void add_column (double[] column_data, string header) {
        if (columns_added >= n_used_indices) return;
        parsed_columns[columns_added].data = column_data;
        parsed_columns[columns_added].header = header;
        columns_added++;
    }

    public void parse () throws Error {
        if (columns_added != n_used_indices) {
            throw new ColumnsParseError.INDEX_ERROR (
                _("Expected %u columns, got %u").printf (n_used_indices, columns_added)
            );
        }

        // Validate lengths
        int expected_length = -1;
        for (uint i = 0; i < n_used_indices; i++) {
            int current_length = parsed_columns[i].data.length;
            if (expected_length == -1) {
                expected_length = current_length;
            } else if (current_length != expected_length) {
                throw new ColumnsParseError.IMPORT_ERROR (
                    _("All columns must have the same length.")
                );
            }
        }
    }

    public string get_header (uint index) {
        return parsed_columns[index_to_rank[index]].header;
    }

    public double[] get_column (uint index) {
        return parsed_columns[index_to_rank[index]].get_data ();
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
