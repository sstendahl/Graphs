// SPDX-License-Identifier: GPL-3.0-or-later
using Gee;
using Gtk;

namespace Graphs {
    [Compact]
    private class Column {
        public double[] data = new double[64];
        public string header = "";
        public uint requests = 0;

        public double[] get_data () {
            if (requests == 0) assert_not_reached ();
            // If this is the last time the data is needed, transfer ownership
            if (requests-- == 1) return (owned) data;
            return data;
        }
    }

    /**
     * Reader class for parsing column-based text files
     */
    public class ColumnsParser : Object {
        private ImportSettings settings;
        private unichar separator;
        private Regex delimiter_regex;

        private ColumnsItemSettings[] items;
        private Bitset used_indices = new Bitset.empty ();
        private uint64 n_used_indices;
        private Column[] columns;
        private int value_size = 0;

        public ColumnsParser (ImportSettings settings) throws Error {
            this.settings = settings;
            var separator = ColumnsSeparator.parse (settings.get_string ("separator"));
            this.separator = separator.as_unichar ();

            var iter = settings.get_value ("items").iterator ();
            items = new ColumnsItemSettings[iter.n_children ()];
            for (int i = 0; i < items.length; i++) {
                var item_settings = ColumnsItemSettings ();
                item_settings.load_from_variant (iter.next_value ());
                items[i] = item_settings;

                if (!item_settings.single_column) {
                    used_indices.add (item_settings.column_x);
                }
                used_indices.add (item_settings.column_y);
                if (item_settings.use_yerr) {
                    used_indices.add (item_settings.yerr_index);
                }
                if (item_settings.use_xerr) {
                    used_indices.add (item_settings.xerr_index);
                }
            }
            this.n_used_indices = used_indices.get_size ();

            this.columns = new Column[n_used_indices];
            for (uint i = 0; i < n_used_indices; i++) {
                columns[i] = new Column ();
            }
            foreach (ColumnsItemSettings item_settings in items) {
                if (!item_settings.single_column) {
                    columns[get_rank (item_settings.column_x)].requests++;
                }
                columns[get_rank (item_settings.column_y)].requests++;
                if (item_settings.use_xerr) {
                    columns[get_rank (item_settings.xerr_index)].requests++;
                }
                if (item_settings.use_yerr) {
                    columns[get_rank (item_settings.yerr_index)].requests++;
                }
            }

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

            var stream = new DataInputStream (settings.file.read ());

            string? line;
            int line_number = 0;
            var bitset_iter = BitsetIter ();
            uint column_index;
            uint column_rank;
            double val;

            int array_size = columns[0].data.length;

            while ((line = stream.read_line ()) != null) {
                if (++line_number <= skip_rows || line.strip ().length == 0) continue;

                string[] str_values = delimiter_regex.split_full (line, -1, 0, 0, (int) max_index + 2);
                if (str_values.length < max_index + 1 && value_size > 0) {
                    throw new ColumnsParseError.INDEX_ERROR (
                        _("Index error in %s, cannot access index %d on line %d, only %d columns were found")
                        .printf (settings.filename, max_index, line_number, str_values.length)
                    );
                }

                // if we reach capacity, grow the arrays.
                if (value_size == array_size) {
                    array_size *= 2;
                    foreach (weak Column column in columns) {
                        column.data.resize (array_size);
                    }
                }

                // We assume, that we have at least one valid index
                bitset_iter.init_first (used_indices, out column_index);
                column_rank = 0;
                do {
                    if (column_index >= str_values.length) break;
                    if (try_evaluate_string (str_values[column_index], out val, separator)) {
                        columns[column_rank++].data[value_size] = val;
                        continue;
                    };

                    // If the data cannot be parsed, treat as header.
                    // But only if there is not already data present
                    if (value_size > 0) {
                        throw new ColumnsParseError.IMPORT_ERROR (
                            _("Cannot import from file, bad value on line %d").printf (line_number)
                        );
                    }
                    columns[column_rank++].header = str_values[column_index];
                    // prevent leading 0 in data
                    value_size = -1;
                } while (bitset_iter.next (out column_index));
                value_size++;
            }

            // shrink to actual size
            foreach (weak Column column in columns) {
                column.data.resize (value_size);
            }

            stream.close ();
        }

        public void add_items (Data data, ItemList itemlist) throws Error {
            foreach (var item_settings in items) {
                uint yrank = get_rank (item_settings.column_y);
                string ylabel = columns[yrank].header;
                double[] ydata = columns[yrank].get_data ();

                double[]? xerr = item_settings.use_xerr ? columns[get_rank (item_settings.xerr_index)].get_data () : null;
                double[]? yerr = item_settings.use_yerr ? columns[get_rank (item_settings.yerr_index)].get_data () : null;

                string xlabel;
                double[] xdata;
                if (item_settings.single_column) {
                    xlabel = "";
                    try {
                        string equation = preprocess_equation (item_settings.equation);
                        xdata = PythonHelper.evaluate_expression (equation, ydata.length, "n");
                    } catch (MathError e) {
                        throw new ColumnsParseError.INVALID_CONFIGURATION (e.message);
                    }
                } else {
                    uint xrank = get_rank (item_settings.column_x);
                    xlabel = columns[xrank].header;
                    xdata = columns[xrank].get_data ();
                }

                Item item = ItemFactory.new_data_item (data, xdata, ydata, xerr, yerr);
                item.xlabel = xlabel;
                item.ylabel = ylabel;
                item.name = settings.filename;
                itemlist.add (item);
            }
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
    }
}
