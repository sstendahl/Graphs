// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;

namespace Graphs {
    public interface CanvasInterface : Widget {
        public abstract string title { get; set; default = ""; }
        public abstract string bottom_label { get; set; default = ""; }
        public abstract string left_label { get; set; default = ""; }
        public abstract string top_label { get; set; default = ""; }
        public abstract string right_label { get; set; default = ""; }

        public abstract int bottom_scale { get; set; default = 0; }
        public abstract int left_scale { get; set; default = 0; }
        public abstract int top_scale { get; set; default = 0; }
        public abstract int right_scale { get; set; default = 0; }

        public abstract bool legend { get; set; default = true; }
        public abstract int legend_position { get; set; default = 0; }

        public abstract double min_bottom { get; set; default = 0; }
        public abstract double max_bottom { get; set; default = 1; }
        public abstract double min_left { get; set; default = 0; }
        public abstract double max_left { get; set; default = 10; }
        public abstract double min_top { get; set; default = 0; }
        public abstract double max_top { get; set; default = 1; }
        public abstract double min_right { get; set; default = 0; }
        public abstract double max_right { get; set; default = 10; }

        public abstract double min_selected { get; set; default = 0; }
        public abstract double max_selected { get; set; default = 0; }

        public abstract Item[] items { set; }
        public abstract bool highlight_enabled { get; set; default = false; }
        public abstract Application application { get; construct set; }
    }

    public interface StyleManagerInterface : Object {
    }
}
