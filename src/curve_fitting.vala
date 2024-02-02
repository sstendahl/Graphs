// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/curve_fitting.ui")]
    public class CurveFittingTool : Adw.Window {
        [GtkChild]
        public unowned Adw.EntryRow custom_equation { get; }

        [GtkChild]
        public unowned Adw.ComboRow equation { get; }

        [GtkChild]
        public unowned Gtk.MenuButton menu_button { get; }

        [GtkChild]
        public unowned Gtk.Box fitting_params { get; }

        [GtkChild]
        public unowned Adw.OverlaySplitView split_view { get; }

        [GtkChild]
        public unowned Adw.ToastOverlay toast_overlay { get; }

        [GtkChild]
        public unowned Gtk.TextView text_view { get; }

        [GtkChild]
        public unowned Gtk.Button confirm_button { get; }

        [GtkChild]
        public unowned Adw.WindowTitle title_widget { get; }

        }

    public class FittingParameter : Object {
        public string name { get; construct set; default = ""; }
        public double initial { get; construct set; default = 1; }
        public string lower_bound { get; construct set; default = "-inf"; }
        public string upper_bound { get; construct set; default = "inf"; }
    }
}

