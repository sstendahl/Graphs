// SPDX-License-Identifier: GPL-3.0-or-later
using Gee;
using Gtk;

namespace Graphs {
    [Compact]
    private class Node {
        public double[] data;
        public Node? next = null;

        public Node (owned double[] array) {
            this.data = array;
        }
    }

    /**
     * Reader class for parsing column-based text files
     */
    public class ColumnsParser : Object {
        private ImportSettings settings;
        private ColumnsSeparator separator;
        private Regex delimiter_regex;

        private Bitset used_indices = new Bitset.empty ();
        private uint64 n_used_indices;
        private Node? head = null;
        private uint n_nodes = 0;
        private string[] headers;

        protected double parse_float_helper { get; set; }
        protected signal bool parse_float_request (string input);

        public ColumnsParser (ImportSettings settings) throws Error {
            this.settings = settings;
            this.separator = ColumnsSeparator.parse (settings.get_string ("separator"));

            string[] item_strings = settings.get_string ("items").split (";;");
            ColumnsItemSettings item_settings = ColumnsItemSettings ();
            foreach (string item_string in item_strings) {
                item_settings.load_from_item_string (item_string);

                if (!item_settings.single_column) {
                    used_indices.add (item_settings.column_x);
                }
                used_indices.add (item_settings.column_y);
            }
            this.n_used_indices = used_indices.get_size ();

            var delimiter_enum = ColumnsDelimiter.parse (settings.get_string ("delimiter"));
            string pattern = delimiter_enum.to_regex_pattern (settings.get_string ("custom-delimiter"));

            try {
                this.delimiter_regex = new Regex (pattern);
            } catch (RegexError e) {
                throw new ColumnsParseError.INVALID_CONFIGURATION (e.message);
            }
        }

        public void parse () throws Error {
            int skip_rows = settings.get_int ("skip-rows");
            int max_index = (int) used_indices.get_maximum ();
            this.headers = new string[max_index + 1];

            var stream = new DataInputStream (settings.file.read ());

            string? line;
            int line_number = 0;
            var bitset_iter = BitsetIter ();
            uint column_index;
            uint array_index;
            weak Node? tail = null;

            while ((line = stream.read_line ()) != null) {
                if (++line_number <= skip_rows || line.strip ().length == 0) continue;

                string[] str_values = delimiter_regex.split_full (line, -1, 0, 0, (int) max_index + 2);
                if (str_values.length < max_index + 1) {
                    throw new ColumnsParseError.INDEX_ERROR (
                        _("Index error in %s, cannot access index %d on line %d, only %d columns were found")
                        .printf (settings.filename, max_index, line_number, str_values.length)
                    );
                }

                var array = new double[n_used_indices];

                // We assume, that we have at least one valid index
                bitset_iter.init_first (used_indices, out column_index);
                array_index = 0;
                do {
                    string expression = str_values[column_index].strip ();
                    if (evaluate_string (expression, out array[array_index++])) continue;

                    // If the data cannot be parsed, treat as header.
                    // But only if there is not already data present
                    if (head != null) {
                        throw new ColumnsParseError.IMPORT_ERROR (
                            _("Cannot import from file, bad value on line %d").printf (line_number)
                        );
                    }

                    headers[column_index] = expression;
                } while (bitset_iter.next (out column_index));

                var node = new Node (array);
                if (head == null) {
                    tail = node;
                    head = (owned) node;
                } else {
                    tail.next = (owned) node;
                    tail = tail.next;
                }
                n_nodes++;
            }

            stream.close ();
        }

        public string get_header (uint index) {
            return headers[index];
        }

        private uint get_rank (uint val) {
            uint current;
            uint rank = 0;
            var bitset_iter = BitsetIter ();
            bitset_iter.init_first (used_indices, out current);
            do {
                if (current == val) return rank;
                rank++;
            } while (bitset_iter.next (out current));
            assert_not_reached ();
        }

        public void get_column (uint index, out double[] values) {
            values = new double[n_nodes];
            uint i = 0;
            uint array_index = get_rank (index);
            for (weak Node? current = head; current != null; current = current.next) {
                values[i++] = current.data[array_index];
            }
        }

        public void get_column_pair (uint index1, uint index2, out double[] values1, out double[] values2) {
            values1 = new double[n_nodes];
            values2 = new double[n_nodes];
            uint i = 0;
            uint array_index1 = get_rank (index1);
            uint array_index2 = get_rank (index2);
            for (weak Node? current = head; current != null; current = current.next) {
                values1[i] = current.data[array_index1];
                values2[i++] = current.data[array_index2];
            }
        }

        private bool evaluate_string (string expression, out double result) {
            if (expression.strip ().length == 0) {
                result = 0;
                return false;
            }

            string normalized = normalize_decimal_separator (expression);
            if (double.try_parse (normalized, out result)) {
                return true;
            }

            // If Vala can't parse, request Python signal
            if (parse_float_request.emit (normalized)) {
                result = this.parse_float_helper;
                return true;
            }

            return false;
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
}
