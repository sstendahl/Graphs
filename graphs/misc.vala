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
}
