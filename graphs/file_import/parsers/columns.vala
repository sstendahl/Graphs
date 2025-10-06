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
        private string filename;

        protected double parse_float_helper { get; set; }
        protected signal bool parse_float_request (string input);

        protected double evaluate_equation_helper { get; set; }
        protected signal bool evaluate_equation_request (string equation, int index);

        public ColumnsParser (ImportSettings settings) throws Error {
            this.settings = settings;
            this.filename = settings.file.get_basename ();
            this.separator = ColumnsSeparator.parse (settings.get_string ("separator"));
            this.column_x = settings.get_int ("column-x");
            this.column_y = settings.get_int ("column-y");

            var delimiter_enum = ColumnsDelimiter.parse (settings.get_string ("delimiter"));
            string pattern = delimiter_enum.to_regex_pattern (settings.get_string ("custom-delimiter"));

            try {
                this.delimiter_regex = new Regex (pattern);
            } catch (RegexError e) {
                throw new ParseError.INVALID_CONFIGURATION (e.message);
            }
        }

        public void parse (out double[] xvalues, out double[] yvalues, out string xlabel, out string ylabel) throws Error {
            var stream = new DataInputStream (settings.file.read ());
            var xvals = new ArrayList<double?> ();
            var yvals = new ArrayList<double?> ();

            string? line;
            int line_number = 0;
            int skip_rows = settings.get_int ("skip-rows");
            bool single_column = settings.get_boolean ("single-column");

            xlabel = "";
            ylabel = "";

            while ((line = stream.read_line ()) != null) {
                line_number++;
                if (line_number <= skip_rows || line.strip ().length == 0) continue;

                string[] values = split_line (line);
                validate_column_indices (values.length, line_number, single_column);

                string xval_str = single_column ? "" : values[column_x];
                string yval_str = values[column_y];

                double? xval = single_column ? null : parse_value (xval_str);
                double? yval = parse_value (yval_str);

                // If we can't parse values and we haven't found data yet, treat as headers
                if ((yval == null || (!single_column && xval == null)) && xvals.size == 0) {
                    if (!single_column) {
                        xlabel = xval_str;
                    }
                    ylabel = yval_str;
                    continue;
                }

                // If we can't parse values but we already have data, it's an error
                if (yval == null || (!single_column && xval == null)) {
                    int actual_line = line_number;
                    throw new ParseError.IMPORT_ERROR (
                        _("Can't import from file, bad value on line %d").printf (actual_line)
                    );
                }

                if (single_column) {
                    xvals.add (generate_x_value (xvals.size));
                } else {
                    xvals.add (xval);
                }
                yvals.add (yval);
            }

            stream.close ();

            if (xvals.size == 0) {
                throw new ParseError.IMPORT_ERROR (_("Unable to import from file: no valid data found"));
            }

            xvalues = new double[xvals.size];
            yvalues = new double[yvals.size];

            for (int i = 0; i < xvals.size; i++) {
                xvalues[i] = xvals[i];
                yvalues[i] = yvals[i];
            }
        }

        private double generate_x_value (int index) throws ParseError {
            string equation = settings.get_string ("single-equation");

            if (evaluate_equation_request.emit (equation, index)) {
                return this.evaluate_equation_helper;
            }

            throw new ParseError.IMPORT_ERROR (
                _("Failed to evaluate equation %s").printf (equation)
            );
        }

        private double? parse_value (string str) {
            if (str.strip ().length == 0) {
                return null;
            }

            string normalized = normalize_decimal_separator (str);
            double result;
            if (double.try_parse (normalized, out result)) {
                return result;
            }

            // If Vala can't parse, request Python signal
            if (parse_float_request.emit (normalized)) {
                return this.parse_float_helper;
            }
            return null;
        }

        private string[] split_line (string line) {
            string[] values = delimiter_regex.split (line);
            for (int i = 0; i < values.length; i++) {
                values[i] = values[i].strip ();
            }
            return values;
        }

        private void validate_column_indices (int num_columns, int line_number, bool single_column) throws ParseError {
            int required_column = single_column ? column_y : int.max (column_x, column_y);

            if (num_columns < required_column + 1) {
                throw new ParseError.INDEX_ERROR (
                    _("Index error in %s, cannot access index %d on line %d, only %d columns were found")
                    .printf (filename, required_column, line_number, num_columns)
                );
            }
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

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/mode-columns.ui")]
    public class ColumnsGroup : Adw.PreferencesGroup {
        [GtkChild]
        public unowned Adw.ComboRow delimiter { get; }
        [GtkChild]
        public unowned Adw.EntryRow custom_delimiter { get; }
        [GtkChild]
        public unowned Adw.ComboRow separator { get; }
        [GtkChild]
        public unowned Adw.SwitchRow single_column { get; }
        [GtkChild]
        public unowned Adw.SpinRow column_x { get; }
        [GtkChild]
        public unowned Adw.SpinRow column_y { get; }
        [GtkChild]
        public unowned Adw.SpinRow skip_rows { get; }
        [GtkChild]
        public unowned Adw.EntryRow single_equation { get; }
        [GtkChild]
        private unowned Button help_button { get; }
        [GtkChild]
        private unowned Popover help_popover { get; }
        [GtkChild]
        private unowned Button equation_help_button { get; }
        [GtkChild]
        private unowned Popover equation_help_popover { get; }

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

            custom_delimiter.set_sensitive (delimiter.get_selected () == ColumnsDelimiter.CUSTOM);
            custom_delimiter.set_text (settings.get_string ("custom-delimiter"));
            custom_delimiter.notify["text"].connect (() => {
                settings.set_string ("custom-delimiter", custom_delimiter.get_text ());
            });

            help_button.clicked.connect (() => {
                help_popover.popup ();
            });

            equation_help_button.clicked.connect (() => {
                equation_help_popover.popup ();
            });

            separator.set_selected (ColumnsSeparator.parse (settings.get_string ("separator")));
            separator.notify["selected"].connect (() => {
                settings.set_string ("separator", ((ColumnsSeparator) separator.get_selected ()).friendly_string ());
            });

            single_column.set_active (settings.get_boolean ("single-column"));
            single_column.notify["active"].connect (() => {
                settings.set_boolean ("single-column", single_column.get_active ());
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

            single_equation.set_text (settings.get_string ("single-equation"));
            single_equation.notify["text"].connect (() => {
                settings.set_string ("single-equation", single_equation.get_text ());
            });
        }
    }
}
