// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Generate Data dialog.
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/generate-data.ui")]
    public class GenerateDataDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.EntryRow equation { get; }

        [GtkChild]
        private unowned Adw.EntryRow xstart { get; }

        [GtkChild]
        private unowned Adw.EntryRow xstop { get; }

        [GtkChild]
        private unowned Adw.SpinRow steps { get; }

        [GtkChild]
        private unowned Adw.ComboRow scale { get; }

        [GtkChild]
        private unowned Button confirm_button { get; }

        [GtkChild]
        private unowned Adw.EntryRow item_name { get; }

        private Window window;
        private GLib.Settings settings;

        public GenerateDataDialog (Window window) {
            Object ();
            this.window = window;
            this.settings = Application.get_settings_child ("generate-data");
            this.equation.set_text (settings.get_string ("equation"));
            this.xstart.set_text (settings.get_string ("xstart"));
            this.xstop.set_text (settings.get_string ("xstop"));
            this.steps.set_value (settings.get_int ("steps"));
            this.scale.set_selected (settings.get_enum ("scale"));
            present (window);
        }

        private void set_confirm_sensitivity () {
            bool invalid = false;
            Widget[] widgets = {equation, xstart, xstop};
            foreach (Widget widget in widgets) {
                invalid = invalid || widget.has_css_class ("error");
            }
            confirm_button.set_sensitive (!invalid);
        }

        [GtkCallback]
        private void on_accept () {
            unowned string equation = this.equation.get_text ();
            unowned string xstart = this.xstart.get_text ();
            unowned string xstop = this.xstop.get_text ();
            int steps = (int) this.steps.get_value ();
            Scale scale = (Scale) this.scale.get_selected ();

            this.settings.set_string ("equation", equation);
            this.settings.set_string ("xstart", xstart);
            this.settings.set_string ("xstop", xstop);
            this.settings.set_int ("steps", steps);
            this.settings.set_enum ("scale", scale);

            unowned string name = item_name.get_text ();
            try {
                Expression expression = expression_to_ast (equation);

                Item item = ItemFactory.new_generated_data_item (window.data, expression, xstart, xstop, steps, scale);
                if (name == "") {
                    item.name = "Y = " + ast_to_expression (expression);
                } else {
                    item.name = name;
                }
                Item[] items = {item};
                window.data.add_items (items);
            } catch (MathError e) { assert_not_reached (); }

            window.data.optimize_limits ();
            close ();
        }

        [GtkCallback]
        private void on_equation_change () {
            if (MathTools.validate_equation (equation.get_text ())) {
                equation.remove_css_class ("error");
            } else {
                equation.add_css_class ("error");
            }
            set_confirm_sensitivity ();
        }

        [GtkCallback]
        private void on_entry_change (Object object, ParamSpec _param_spec) {
            var entry = object as Adw.EntryRow;
            if (try_evaluate_string (entry.get_text ())) {
                entry.remove_css_class ("error");
            } else {
                entry.add_css_class ("error");
            }
            set_confirm_sensitivity ();
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
