// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;

namespace Graphs {
    /**
     * Custom Canvas implementation.
     */
    public class Canvas : DrawingArea {
        public bool hide_unselected { get; set; default = false; }
        public int mode { get; set; default = 0; }
        public ListModel items { get; construct set; }

        public double min_selected { get; set; default = 0; }
        public double max_selected { get; set; default = 0; }

        public signal void edit_request (string id);
        public signal void view_changed ();
        public signal void view_action ();

        protected signal void save_request (File file, string format, int dpi, bool transparent);
        public void save (File file, string format, int dpi, bool transparent) {
            this.save_request.emit (file, format, dpi, transparent);
        }

        protected signal void zoom_request (double factor);
        public void zoom (double factor) {
            this.zoom_request.emit (factor);
        }
    }
}
