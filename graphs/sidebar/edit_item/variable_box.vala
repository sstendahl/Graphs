// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/variable.ui")]
    private class EditItemVariableItemBox : Gtk.Box {
        [GtkChild]
        private unowned Adw.PreferencesGroup group { get; }
        [GtkChild]
        private unowned Adw.EntryRow value { get; }
        [GtkChild]
        private unowned Adw.EntryRow min { get; }
        [GtkChild]
        private unowned Adw.EntryRow max { get; }
        [GtkChild]
        private unowned Adw.EntryRow step { get; }

        private VariableItem item;

        public EditItemVariableItemBox (VariableItem item) {
            this.item = item;
            // Translators: Formatted with the name of a variable
            group.set_title (_("Variable %s").printf (item.variable));

            item.notify["value"].connect (update);
            item.notify["min"].connect (update);
            item.notify["max"].connect (update);
            item.notify["step"].connect (update);
            update ();
        }

        private void update () {
            set_entry (value, item.value);
            set_entry (min, item.min);
            set_entry (max, item.max);
            set_entry (step, item.get_effective_step ());
        }

        private static void set_entry (Adw.EntryRow entry, double val) {
            double current;
            if (try_evaluate_string (entry.get_text (), out current) && current == val) return;
            entry.set_text (MathTools.prettyprint_double (val));
            entry.set_show_apply_button (false);
            entry.set_show_apply_button (true);
        }

        private bool is_valid (Adw.EntryRow entry, out double val) {
            if (!try_evaluate_string (entry.get_text (), out val)) return false;
            if (!val.is_finite ()) return false;
            if (entry == step) return val > 0;
            if (entry == min) return val <= item.max;
            if (entry == max) return val >= item.min;
            return true;
        }

        [GtkCallback]
        private void on_entry_change (Object object, ParamSpec spec) {
            var entry = (Adw.EntryRow) object;
            double val;
            if (is_valid (entry, out val)) {
                entry.remove_css_class ("error");
                entry.set_show_apply_button (true);
            } else {
                entry.add_css_class ("error");
                entry.set_show_apply_button (false);
            }
        }

        [GtkCallback]
        private void on_entry_apply (Adw.EntryRow entry) {
            double val;
            if (!is_valid (entry, out val)) return;

            if (entry == value) {
                item.value = val;
            } else if (entry == min) {
                item.min = val;
            } else if (entry == max) {
                item.max = val;
            } else {
                item.step = val;
            }
            if (entry != value) item.fit_value ();

            // workaround button not disappearing when pressed
            entry.set_show_apply_button (false);
            entry.set_show_apply_button (true);
        }
    }
}
