// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/figure-settings/axis-limits-row.ui")]
    public class AxisLimitsRow : Adw.ActionRow {

        [GtkChild]
        private unowned Gtk.Text min_text { get; }

        [GtkChild]
        private unowned Gtk.Text max_text { get; }

        [GtkChild]
        private unowned Gtk.ToggleButton lock_button { get; }

        public double min { get; set; }
        public double max { get; set; }
        public bool locked { get; set; }

        public signal void applied ();

        construct {
            notify["min"].connect (() => min_text.text = MathTools.prettyprint_double (min));
            notify["max"].connect (() => max_text.text = MathTools.prettyprint_double (max));
            notify["locked"].connect (update_lock_button);

            min_text.text = MathTools.prettyprint_double (min);
            max_text.text = MathTools.prettyprint_double (max);
            update_lock_button ();
        }

        public void focus_limit (bool maximum) {
            (maximum ? max_text : min_text).grab_focus ();
        }

        private void update_lock_button () {
            lock_button.icon_name = locked ? "padlock-closed-symbolic" : "padlock-open-symbolic";
            lock_button.tooltip_text = locked ? _("Unlock Axis Limits") : _("Lock Axis Limits");
        }

        private void apply (Gtk.Text text) {
            bool maximum = text == max_text;
            double new_val;
            if (!try_evaluate_string (text.text, out new_val)) return;

            if (maximum) max = new_val;
            else min = new_val;
            text.text = MathTools.prettyprint_double (new_val);
            applied ();
        }

        [GtkCallback]
        private void on_activate (Gtk.Text text) {
            apply (text);
        }

        [GtkCallback]
        private void on_focus_changed (Object object, ParamSpec spec) {
            var text = (Gtk.Text) object;
            if (!text.has_focus) apply (text);
        }

        [GtkCallback]
        private void on_text_changed (Object object, ParamSpec spec) {
            var text = (Gtk.Text) object;
            if (try_evaluate_string (text.text)) {
                text.remove_css_class ("error");
            } else {
                text.add_css_class ("error");
            }
        }
    }
}
