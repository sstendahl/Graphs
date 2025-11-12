// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;

namespace Graphs {
    /**
     * Custom Canvas implementation.
     */
    public class Canvas : DrawingArea {
        public int mode { get; set; default = 0; }

        public double min_selected { get; set; default = 0; }
        public double max_selected { get; set; default = 0; }

        public signal void edit_request (string id);
        public signal void view_changed ();

        protected signal void zoom_request (double factor);
        public void zoom (double factor) {
            this.zoom_request.emit (factor);
        }
    }
}
