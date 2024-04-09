// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    public class FittingParameter : Object {
        public string name { get; construct set; default = ""; }
        public double initial { get; construct set; default = 1; }
        public string lower_bound { get; construct set; default = "-inf"; }
        public string upper_bound { get; construct set; default = "inf"; }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/fitting-parameters.ui")]
    public class FittingParameterBox : Box {

        [GtkChild]
        private unowned Label label { get; }

        [GtkChild]
        public unowned Adw.EntryRow initial { get; }

        [GtkChild]
        public unowned Adw.EntryRow upper_bound { get; }

        [GtkChild]
        public unowned Adw.EntryRow lower_bound { get; }

        public FittingParameterBox (FittingParameter param) {
            string msg = _("Fitting Parameters for %s").printf (param.name);
            this.label.set_markup (@"<b> $msg: </b>");
            this.initial.set_text (param.initial.to_string ());
        }

        public void set_bounds_visible (bool visible) {
            this.upper_bound.set_visible (visible);
            this.lower_bound.set_visible (visible);
        }
    }
}
