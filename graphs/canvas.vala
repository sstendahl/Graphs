// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;

namespace Graphs {
    public class Canvas : DrawingArea {
        public bool hide_unselected { get; set; default = false; }
        public int mode { get; set; default = 0; }

        public double min_selected { get; set; default = 0; }
        public double max_selected { get; set; default = 0; }

        public signal void edit_request (string id);
        public signal void view_changed ();
    }
}
