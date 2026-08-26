// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/generated-data.ui")]
    public class EditItemGeneratedDataItemBox : Gtk.Box {
        [GtkChild]
        private unowned EditItemEquationGroup equation_group { get; }
        [GtkChild]
        private unowned Adw.EntryRow xstart { get; }
        [GtkChild]
        private unowned Adw.EntryRow xstop { get; }
        [GtkChild]
        private unowned Adw.SpinRow steps { get; }
        [GtkChild]
        private unowned Adw.ComboRow scale { get; }

        private GeneratedDataItem item;

        public EditItemGeneratedDataItemBox (GeneratedDataItem item) {
            this.item = item;
            equation_group.setup (item);

            xstart.set_text (item.xstart);
            xstop.set_text (item.xstop);

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

        [GtkCallback]
        private void on_entry_change (Object object, ParamSpec spec) {
            var entry = (Adw.EntryRow) object;
            if (try_evaluate_string (entry.get_text ())) {
                entry.remove_css_class ("error");
                entry.set_show_apply_button (true);
            } else {
                entry.add_css_class ("error");
                entry.set_show_apply_button (false);
            }
        }

        [GtkCallback]
        private void on_entry_apply (Gtk.Editable editable) {
            item.set (editable.get_buildable_id (), editable.get_text ());
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
