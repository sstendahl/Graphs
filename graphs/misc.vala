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
