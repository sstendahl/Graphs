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

        public string friendly_string () {
            switch (this) {
                case BOTTOM: return "bottom";
                case TOP: return "top";
                default: assert_not_reached ();
            }
        }
    }

    public enum YPosition {
        LEFT,
        RIGHT;

        public string friendly_string () {
            switch (this) {
                case LEFT: return "left";
                case RIGHT: return "right";
                default: assert_not_reached ();
            }
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
            switch (str) {
                case "linear": return LINEAR;
                case "log": return LOG;
                case "log2": return LOG2;
                case "radians": return RADIANS;
                case "squareroot": return SQUAREROOT;
                case "inverse": return INVERSE;
                default: assert_not_reached ();
            }
        }
    }

    public static string scale_to_string (Scale scale) {
        return scale.to_string ()[13:].down ();
    }

    public enum LegendPosition {
        BEST,
        UPPER_RIGHT,
        UPPER_LEFT,
        LOWER_LEFT,
        LOWER_RIGHT,
        CENTER_LIGHT,
        CENTER_RIGHT,
        LOWER_CENTER,
        UPPER_CENTER,
        CENTER;

        public static LegendPosition from_string (string str) {
            switch (str) {
                case "best": return BEST;
                case "upper right": return UPPER_RIGHT;
                case "upper left": return UPPER_LEFT;
                case "lower left": return LOWER_LEFT;
                case "lower right": return LOWER_RIGHT;
                case "center left": return CENTER_LIGHT;
                case "center right": return CENTER_RIGHT;
                case "lower center": return LOWER_CENTER;
                case "upper center": return UPPER_CENTER;
                case "center": return CENTER;
                default: assert_not_reached ();
            }
        }

        public string friendly_string () {
            switch (this) {
                case BEST: return "best";
                case UPPER_RIGHT: return "upper right";
                case UPPER_LEFT: return "upper left";
                case LOWER_LEFT: return "lower left";
                case LOWER_RIGHT: return "lower right";
                case CENTER_LIGHT: return "center left";
                case CENTER_RIGHT: return "center right";
                case LOWER_CENTER: return "lower center";
                case UPPER_CENTER: return "upper center";
                case CENTER: return "center";
                default: assert_not_reached ();
            }
        }
    }

    // Python cannot bind Enum instance methods
    public static string legend_position_to_string (LegendPosition pos) {
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
