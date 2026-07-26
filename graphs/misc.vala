// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;

namespace Graphs {
    public ListModel get_mplstyle_file_filters () {
        var filter = Tools.create_file_filter (
            C_("file-filter", "Matplotlib Style File"), "mplstyle"
        );
        return Tools.create_file_filters (false, filter);
    }

    public enum XPosition {
        BOTTOM,
        TOP;

        public unowned string friendly_string () {
            EnumClass enumc = (EnumClass) typeof (XPosition).class_ref ();
            unowned EnumValue? eval = enumc.get_value (this);
            return eval.value_nick;
        }
    }

    public enum YPosition {
        LEFT,
        RIGHT;

        public unowned string friendly_string () {
            EnumClass enumc = (EnumClass) typeof (YPosition).class_ref ();
            unowned EnumValue? eval = enumc.get_value (this);
            return eval.value_nick;
        }
    }

    public enum Markerstyle {
        NONE,
        POINT,
        PIXEL,
        CIRCLE,
        TRIANGLE_DOWN,
        TRIANGLE_UP,
        TRIANGLE_LEFT,
        TRIANGLE_RIGHT,
        OCTAGON,
        SQUARE,
        PENTAGON,
        STAR,
        HEXAGON_1,
        HEXAGON_2,
        PLUS,
        X,
        DIAMOND,
        THIN_DIAMOND,
        VERTICAL_LINE,
        HORIZONTAL_LINE,
        FILLED_PLUS,
        FILLED_X;

        public static Markerstyle from_style (string str) {
            switch (str) {
                case "none": return NONE;
                case ".": return POINT;
                case ",": return PIXEL;
                case "o": return CIRCLE;
                case "v": return TRIANGLE_DOWN;
                case "^": return TRIANGLE_UP;
                case "<": return TRIANGLE_LEFT;
                case ">": return TRIANGLE_RIGHT;
                case "8": return OCTAGON;
                case "s": return SQUARE;
                case "p": return PENTAGON;
                case "*": return STAR;
                case "h": return HEXAGON_1;
                case "H": return HEXAGON_2;
                case "+": return PLUS;
                case "x": return X;
                case "D": return DIAMOND;
                case "d": return THIN_DIAMOND;
                case "|": return VERTICAL_LINE;
                case "_": return HORIZONTAL_LINE;
                case "P": return FILLED_PLUS;
                case "X": return FILLED_X;
                default: assert_not_reached ();
            }
        }
    }

    public enum Linestyle {
        NONE,
        SOLID,
        DOTTED,
        DASHED,
        DASHDOT;

        public static Linestyle from_string (string str) {
            EnumClass enumc = (EnumClass) typeof (Linestyle).class_ref ();
            unowned EnumValue? eval = enumc.get_value_by_nick (str);
            return (Linestyle) eval.value;
        }
    }

    public enum EquationLinestyle {
        SOLID,
        DOTTED,
        DASHED,
        DASHDOT;

        public static EquationLinestyle from_string (string str) {
            EnumClass enumc = (EnumClass) typeof (EquationLinestyle).class_ref ();
            unowned EnumValue? eval = enumc.get_value_by_nick (str);
            return (EquationLinestyle) eval.value;
        }
    }

    public enum TickDirection {
        IN,
        OUT;

        public static TickDirection from_string (string str) {
            EnumClass enumc = (EnumClass) typeof (TickDirection).class_ref ();
            unowned EnumValue? eval = enumc.get_value_by_nick (str);
            return (TickDirection) eval.value;
        }
    }

    public enum Scale {
        LINEAR,
        LOG,
        LOG2,
        RADIANS,
        SQUAREROOT,
        INVERSE;

        public static Scale from_string (string str) {
            EnumClass enumc = (EnumClass) typeof (Scale).class_ref ();
            unowned EnumValue? eval = enumc.get_value_by_nick (str);
            return (Scale) eval.value;
        }

        public unowned string friendly_string () {
            EnumClass enumc = (EnumClass) typeof (Scale).class_ref ();
            unowned EnumValue? eval = enumc.get_value (this);
            return eval.value_nick;
        }

        public bool is_logarithmic () {
            return this == LOG || this == LOG2;
        }

        public bool is_nonzero () {
            return is_logarithmic () || this == SQUAREROOT;
        }
    }

    // Python cannot bind Enum instance methods
    public static unowned string scale_to_string (Scale scale) {
        return scale.friendly_string ();
    }

    public enum LegendPosition {
        BEST,
        UPPER_RIGHT,
        UPPER_LEFT,
        LOWER_LEFT,
        LOWER_RIGHT,
        CENTER_LEFT,
        CENTER_RIGHT,
        LOWER_CENTER,
        UPPER_CENTER,
        CENTER;

        public static LegendPosition from_string (string str) {
            EnumClass enumc = (EnumClass) typeof (LegendPosition).class_ref ();
            unowned EnumValue? eval = enumc.get_value_by_nick (str);
            return (LegendPosition) eval.value;
        }

        public unowned string friendly_string () {
            EnumClass enumc = (EnumClass) typeof (LegendPosition).class_ref ();
            unowned EnumValue? eval = enumc.get_value (this);
            return eval.value_nick;
        }
    }

    // Python cannot bind Enum instance methods
    public unowned string legend_position_to_string (LegendPosition pos) {
        return pos.friendly_string ();
    }

    public enum ChangeType {
        ITEM_PROPERTY_CHANGED,
        ITEM_ADDED,
        ITEM_REMOVED,
        ITEMS_SWAPPED,
        FIGURE_SETTINGS_CHANGED
    }

    public enum Mode {
        PAN,
        ZOOM,
        SELECT
    }
}
