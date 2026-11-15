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
        private unowned Adw.SpinRow steps { get; }
        [GtkChild]
        private unowned Adw.ComboRow scale { get; }

        private VariableItem item;

        public EditItemVariableItemBox (VariableItem item) {
            this.item = item;
            // Translators: Formatted with the name of a variable
            group.set_title (_("Variable %s").printf (item.variable));

            item.notify["value"].connect (update);
            item.notify["min"].connect (update);
            item.notify["max"].connect (update);
            item.notify["scale"].connect (update);
            update ();

            item.bind_property (
                "steps",
                steps,
                "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "scale",
                scale,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
        }

        private void update () {
            set_entry (value, item.value);
            set_entry (min, item.min);
            set_entry (max, item.max);
        }

        private void set_entry (Adw.EntryRow entry, double val) {
            double current;
            if (!try_evaluate_string (entry.get_text (), out current) || current != val) {
                entry.set_text (MathTools.prettyprint_double (val));
                // There is nothing to apply until the text is edited
                entry.set_show_apply_button (false);
            }
            // What is valid depends on the scale and on the other entries
            check (entry);
        }

        private bool is_valid (Adw.EntryRow entry, out double val) {
            if (!try_evaluate_string (entry.get_text (), out val)) return false;
            if (!val.is_finite () || !item.supports_scale (val)) return false;
            if (entry == min) return val <= item.max;
            if (entry == max) return val >= item.min;
            return true;
        }

        [GtkCallback]
        private void on_entry_change (Object object, ParamSpec spec) {
            check ((Adw.EntryRow) object);
        }

        private void check (Adw.EntryRow entry) {
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

            item.set (entry.get_buildable_id (), val);
            if (entry != value) item.fit_value ();

            // workaround button not disappearing when pressed
            entry.set_show_apply_button (false);
            entry.set_show_apply_button (true);
        }

        [GtkCallback]
        private int on_steps_input (out double val) {
            if (try_evaluate_string (steps.get_text (), out val)) {
                return 1;
            } else {
                return Gtk.INPUT_ERROR;
            }
        }
    }
}
