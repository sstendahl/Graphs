// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;

namespace Graphs {
    public const string[] LIMIT_NAMES = {
        "min-bottom", "max-bottom", "min-top", "max-top",
        "min-left", "max-left", "min-right", "max-right",
    };

    public const string[] DIRECTION_NAMES = {
        "bottom", "top", "left", "right"
    };

    public ListModel get_mplstyle_file_filters () {
        var filter = Tools.create_file_filter (
            C_("file-filter", "Matplotlib Style File"), "mplstyle"
        );
        return Tools.create_file_filters (false, filter);
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
}
