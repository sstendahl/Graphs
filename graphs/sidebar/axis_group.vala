// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/figure-settings/axis-group.ui")]
    public class AxisGroup : Adw.PreferencesGroup {

        [GtkChild]
        private unowned Adw.EntryRow label_row { get; }

        [GtkChild]
        private unowned Adw.EntryRow min_row { get; }

        [GtkChild]
        private unowned Adw.EntryRow max_row { get; }

        [GtkChild]
        private unowned Adw.ComboRow scale_row { get; }

        public double min { get; set; }
        public double max { get; set; }
        public bool min_locked { get; set; }
        public bool max_locked { get; set; }

        public signal void applied ();

        construct {
            bind_property ("min", min_row, "text", BindingFlags.SYNC_CREATE, prettyprint_transform);
            bind_property ("max", max_row, "text", BindingFlags.SYNC_CREATE, prettyprint_transform);
        }

        public void bind (FigureSettings figure_settings, string direction) {
            figure_settings.bind_property (direction + "-label", label_row, "text", SYNC);
            figure_settings.bind_property (direction + "-scale", scale_row, "selected", SYNC);
            figure_settings.bind_property ("min-" + direction, this, "min", SYNC);
            figure_settings.bind_property ("max-" + direction, this, "max", SYNC);
            figure_settings.bind_property ("lock-min-" + direction, this, "min-locked", SYNC);
            figure_settings.bind_property ("lock-max-" + direction, this, "max-locked", SYNC);
        }

        public void focus_row (string name) {
            (name == "label" ? label_row : name == "min" ? min_row : max_row).grab_focus ();
        }

        private static bool prettyprint_transform (Binding binding, Value source, ref Value target) {
            target.set_string (MathTools.prettyprint_double (source.get_double ()));
            return true;
        }

        [GtkCallback]
        private void on_lock_toggled (Object object, ParamSpec spec) {
            var button = (Gtk.ToggleButton) object;
            button.icon_name = button.active ? "padlock-closed-symbolic" : "padlock-open-symbolic";
            button.tooltip_text = button.active ? _("Unlock Limit") : _("Lock Limit");
        }

        [GtkCallback]
        private void on_apply (Adw.EntryRow row) {
            double val;
            if (!try_evaluate_string (row.text, out val)) return;
            if (row == min_row) min = val;
            else max = val;
            applied ();

            // workaround button not disappearing when pressed
            row.show_apply_button = false;
            row.show_apply_button = true;
        }

        [GtkCallback]
        private void on_text_changed (Object object, ParamSpec spec) {
            var row = (Adw.EntryRow) object;
            if (try_evaluate_string (row.text)) {
                row.remove_css_class ("error");
            } else {
                row.add_css_class ("error");
            }
        }
    }
}
