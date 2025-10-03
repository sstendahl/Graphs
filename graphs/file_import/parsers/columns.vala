// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {
    public errordomain ParseError {
        INDEX_ERROR,
        IMPORT_ERROR,
        INVALID_CONFIGURATION
    }

    enum ColumnsDelimiter {
        WHITESPACE,
        TAB,
        COLON,
        SEMICOLON,
        COMMA,
        PERIOD,
        CUSTOM;

        public string friendly_string () {
            return this.to_string ()[25:].down ();
        }

        public static ColumnsDelimiter parse (string delimiter) {
            switch (delimiter) {
                case "whitespace": return ColumnsDelimiter.WHITESPACE;
                case "tab": return ColumnsDelimiter.TAB;
                case "colon": return ColumnsDelimiter.COLON;
                case "semicolon": return ColumnsDelimiter.SEMICOLON;
                case "comma": return ColumnsDelimiter.COMMA;
                case "period": return ColumnsDelimiter.PERIOD;
                case "custom": return ColumnsDelimiter.CUSTOM;
                default: assert_not_reached ();
            }
        }

        public string to_regex_pattern (string custom_delimiter) throws ParseError {
            switch (this) {
                case WHITESPACE: return "\\s+";
                case TAB: return "\\t";
                case COLON: return ":";
                case SEMICOLON: return ";";
                case COMMA: return ",";
                case PERIOD: return "\\.";
                case CUSTOM:
                    if (custom_delimiter.length == 0) {
                        throw new ParseError.INVALID_CONFIGURATION (
                            _("Custom delimiter cannot be empty")
                        );
                    }
                    return custom_delimiter;
                default: assert_not_reached ();
            }
        }
    }

    enum ColumnsSeparator {
        COMMA,
        PERIOD;

        public string friendly_string () {
            return this.to_string ()[25:].down ();
        }

        public static ColumnsSeparator parse (string separator) {
            switch (separator) {
                case "comma": return ColumnsSeparator.COMMA;
                case "period": return ColumnsSeparator.PERIOD;
                default: assert_not_reached ();
            }
        }

        public string get_decimal_char () {
            return this == COMMA ? "," : ".";
        }
    }

    /**
     * Reader class for parsing column-based text files
     */
    public class ColumnsParser : Object {
        private ImportSettings settings;
        private int column_x;
        private int column_y;
        private ColumnsSeparator separator;
        private Regex delimiter_regex;
        private int skip_rows;

        public ColumnsParser (ImportSettings settings) throws Error {
            this.settings = settings;
            this.column_x = settings.get_int ("column-x");
            this.column_y = settings.get_int ("column-y");
            this.separator = ColumnsSeparator.parse (settings.get_string ("separator"));
            this.skip_rows = settings.get_int ("skip-rows");

            var delimiter_enum = ColumnsDelimiter.parse (settings.get_string ("delimiter"));
            string pattern = delimiter_enum.to_regex_pattern (settings.get_string ("custom-delimiter"));

            try {
                this.delimiter_regex = new Regex (pattern);
            } catch (RegexError e) {
                throw new ParseError.INVALID_CONFIGURATION (e.message);
            }
        }

        public void parse (out double[] xdata, out double[] ydata,
                          out string? xlabel, out string? ylabel) throws Error {
            var stream = new DataInputStream (settings.file.read ());

            var xdata_list = new ArrayList<double?> ();
            var ydata_list = new ArrayList<double?> ();
            xlabel = null;
            ylabel = null;

            string? line;
            int index = 0;
            int data_index = 0;
            bool parsed = false;
            bool parsing_mode = false;

            while ((line = stream.read_line ()) != null) {
                index++;

                if (index <= skip_rows) {
                    continue;
                }

                line = line.strip ();
                if (line.length == 0) {
                    continue;
                }

                string[] values = split_line (line);

                if (values.length > 1) {
                    validate_column_indices (values.length);
                }


                if (values.length == 1) {
                    parsed = parse_single_column (values[0], data_index,
                                                  xdata_list, ydata_list);
                } else {
                    parsed = parse_multi_column (values[column_x], values[column_y],
                                                xdata_list, ydata_list);
                }

                if (parsed) {
                    parsing_mode = true;
                    data_index++;
                }
                if (!parsing_mode) {
                    extract_headers (values, ref xlabel, ref ylabel);
                }
            }

            stream.close ();

            if (xdata_list.size == 0) {
                throw new ParseError.IMPORT_ERROR (
                    _("Unable to import from file")
                );
            }

            xdata = new double[xdata_list.size];
            ydata = new double[ydata_list.size];
            for (int i = 0; i < xdata_list.size; i++) {
                xdata[i] = xdata_list[i];
                ydata[i] = ydata_list[i];
            }
        }

        private string[] split_line (string line) {
            string[] values = delimiter_regex.split (line);

            for (int i = 0; i < values.length; i++) {
                values[i] = values[i].strip ();
            }

            return values;
        }

        private void validate_column_indices (int num_columns) throws ParseError {
            if (column_x >= num_columns || column_y >= num_columns) {
                int bad_column = int.max (column_x, column_y);
                throw new ParseError.INDEX_ERROR (
                    _("Index Error: Cannot access column %d, only %d columns were found")
                    .printf (bad_column, num_columns)
                );
            }
        }

        private bool parse_multi_column (string x_value, string y_value,
                                         ArrayList<double?> xdata,
                                         ArrayList<double?> ydata) {
            // Placeholder assignment to prevent `The name `y' does not exist in the context of` errors
            double x = 0.0;
            double y = 0.0;

            string x_normalized = normalize_decimal_separator (x_value);
            string y_normalized = normalize_decimal_separator (y_value);

            if (double.try_parse (x_normalized, out x) && double.try_parse (y_normalized, out y)) {
                xdata.add (x);
                ydata.add (y);
                return true;
            }
            return false;
        }

        private bool parse_single_column (string y_value, int index,
                                          ArrayList<double?> xdata,
                                          ArrayList<double?> ydata) {
            // Placeholder assignment to prevent `The name `y' does not exist in the context of` errors
            double y = 0.0;
            string normalized = normalize_decimal_separator (y_value);

            if (double.try_parse (normalized, out y)) {
                ydata.add (y);
                xdata.add ((double) index);
                return true;
            }
            return false;
        }

        private void extract_headers (string[] values,
                                     ref string? xlabel,
                                     ref string? ylabel) {
            if (values.length == 1) {
                if (values[0].length > 0) {
                    ylabel = values[0];
                }
            } else {
                if (values[column_x].length > 0) {
                    xlabel = values[column_x];
                }
                if (values[column_y].length > 0) {
                    ylabel = values[column_y];
                }
            }
        }

        private string normalize_decimal_separator (string str) {
            string decimal_char = separator.get_decimal_char ();
            string thousands_char = decimal_char == "," ? "." : ",";
            string cleaned = str.replace (thousands_char, "");

            if (decimal_char != ".") {
                cleaned = cleaned.replace (decimal_char, ".");
            }

            return cleaned;
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/mode-columns.ui")]
    public class ColumnsGroup : Adw.PreferencesGroup {
        [GtkChild]
        public unowned Adw.ComboRow delimiter { get; }
        [GtkChild]
        public unowned Adw.EntryRow custom_delimiter { get; }
        [GtkChild]
        public unowned Adw.ComboRow separator { get; }
        [GtkChild]
        public unowned Adw.SpinRow column_x { get; }
        [GtkChild]
        public unowned Adw.SpinRow column_y { get; }
        [GtkChild]
        public unowned Adw.SpinRow skip_rows { get; }

        public ColumnsGroup (ImportSettings settings) {
            setup_ui (settings);
        }

        private void setup_ui (ImportSettings settings) {
            delimiter.set_selected (ColumnsDelimiter.parse (settings.get_string ("delimiter")));
            delimiter.notify["selected"].connect (() => {
                ColumnsDelimiter selected = (ColumnsDelimiter) delimiter.get_selected ();
                settings.set_string ("delimiter", selected.friendly_string ());
                custom_delimiter.set_sensitive (selected == ColumnsDelimiter.CUSTOM);
            });

            custom_delimiter.set_text (settings.get_string ("custom-delimiter"));
            custom_delimiter.notify["text"].connect (() => {
                settings.set_string ("custom-delimiter", custom_delimiter.get_text ());
            });

            separator.set_selected (ColumnsSeparator.parse (settings.get_string ("separator")));
            separator.notify["selected"].connect (() => {
                settings.set_string ("separator", ((ColumnsSeparator) separator.get_selected ()).friendly_string ());
            });

            column_x.set_value (settings.get_int ("column-x"));
            column_x.notify["value"].connect (() => {
                settings.set_int ("column-x", (int) column_x.get_value ());
            });

            column_y.set_value (settings.get_int ("column-y"));
            column_y.notify["value"].connect (() => {
                settings.set_int ("column-y", (int) column_y.get_value ());
            });

            skip_rows.set_value (settings.get_int ("skip-rows"));
            skip_rows.notify["value"].connect (() => {
                settings.set_int ("skip-rows", (int) skip_rows.get_value ());
            });
        }
    }
}
