// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/curve_fitting.ui")]
    public class CurveFittingTool : Adw.Window {
        public FigureSettings figure_settings { get; construct set; }
        [GtkChild]
        public unowned Adw.EntryRow equation { get; }

        [GtkChild]
        public unowned Gtk.Box fitting_params { get; }

        [GtkChild]
        public unowned Adw.ToastOverlay toast_overlay { get; }

        [GtkChild]
        public unowned Gtk.TextView text_view { get; }

        [GtkChild]
        public unowned Gtk.Button confirm_button { get; }
        }

    public class FittingParameter : Object {
        public string name { get; construct set; default = ""; }
        public double initial { get; construct set; default = 1; }
        public string lower_bound { get; construct set; default = "-inf"; }
        public string upper_bound { get; construct set; default = "inf"; }
    }
}
