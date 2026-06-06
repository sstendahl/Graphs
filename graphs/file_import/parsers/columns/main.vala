// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public errordomain ColumnsParseError {
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

        public unowned string friendly_string () {
            EnumClass enumc = (EnumClass) typeof (ColumnsDelimiter).class_ref ();
            unowned EnumValue? eval = enumc.get_value (this);
            return eval.value_nick;
        }

        public static ColumnsDelimiter parse (string delimiter) {
            EnumClass enumc = (EnumClass) typeof (ColumnsDelimiter).class_ref ();
            unowned EnumValue? eval = enumc.get_value_by_nick (delimiter);
            return (ColumnsDelimiter) eval.value;
        }

        public unowned string to_regex_pattern (string custom_delimiter) throws ColumnsParseError {
            switch (this) {
                case WHITESPACE: return "\\s+";
                case TAB: return "\\t";
                case COLON: return ":";
                case SEMICOLON: return ";";
                case COMMA: return ",";
                case PERIOD: return "\\.";
                case CUSTOM:
                    if (custom_delimiter.length == 0) {
                        throw new ColumnsParseError.INVALID_CONFIGURATION (
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

        public unowned string friendly_string () {
            EnumClass enumc = (EnumClass) typeof (ColumnsSeparator).class_ref ();
            unowned EnumValue? eval = enumc.get_value (this);
            return eval.value_nick;
        }

        public unichar as_unichar () {
            return this == ColumnsSeparator.COMMA ? ',' : '.';
        }

        public static ColumnsSeparator parse (string separator) {
            EnumClass enumc = (EnumClass) typeof (ColumnsSeparator).class_ref ();
            unowned EnumValue? eval = enumc.get_value_by_nick (separator);
            return (ColumnsSeparator) eval.value;
        }
    }

    public struct ColumnsItemSettings {
        public int column_x;
        public int column_y;
        public int xerr_index;
        public int yerr_index;
        public bool single_column;
        public bool use_xerr;
        public bool use_yerr;
        public string equation;

        public void load_from_variant (Variant variant) {
            variant.get ("(iiiibbbs)",
                out column_x,
                out column_y,
                out xerr_index,
                out yerr_index,
                out single_column,
                out use_xerr,
                out use_yerr,
                out equation
            );
        }

        public Variant to_variant () {
            return new Variant ("(iiiibbbs)",
                column_x,
                column_y,
                xerr_index,
                yerr_index,
                single_column,
                use_xerr,
                use_yerr,
                equation
            );
        }
    }
}
