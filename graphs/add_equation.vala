// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * Add Equation dialog.
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/add-equation.ui")]
    private class AddEquationDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.EntryRow equation { get; }

        [GtkChild]
        private unowned Gtk.Button confirm_button { get; }

        [GtkChild]
        private unowned Adw.EntryRow item_name { get; }

        [GtkChild]
        private unowned Adw.PreferencesGroup variables_group { get; }

        private Window window;
        private Settings settings;

        private string[] variables = {};
        private Adw.PreferencesRow[] variable_rows = {};
        private HashTable<string, string> entered_values = new HashTable<string, string> (str_hash, str_equal);

        public AddEquationDialog (Window window) {
            Object ();
            this.window = window;
            this.settings = Application.get_settings_child ("add-equation");
            this.equation.set_text (settings.get_string ("equation"));
            present (window);
        }

        [GtkCallback]
        private void on_accept () {
            unowned string equation_str = this.equation.get_text ();
            this.settings.set_string ("equation", equation_str);
            unowned string name = item_name.get_text ();

            try {
                Ast expression = expression_to_ast (equation_str);

                Item item = new EquationItem (window.data.selected_style_params, expression) {
                    name = name == "" ? "Y = " + ast_to_expression (expression) : name,
                };
                Item[] items = {item};
                foreach (unowned string variable in variables) {
                    if (window.data.get_variable_item (variable) != null) continue;
                    double val;
                    get_value (variable, out val);
                    items += new VariableItem (variable, val);
                }
                window.data.add_items (items);
            } catch (MathError e) { assert_not_reached (); }

            window.data.optimize_limits ();
            close ();
        }

        private bool get_value (string variable, out double val) {
            VariableItem? existing = window.data.get_variable_item (variable);
            if (existing != null) {
                val = existing.value;
                return true;
            }

            unowned string? text = entered_values.lookup (variable);
            if (text == null) {
                val = VariableItem.DEFAULT_VALUE;
                return true;
            }
            if (try_evaluate_string (text, out val) && val.is_finite ()) return true;
            val = VariableItem.DEFAULT_VALUE;
            return false;
        }

        private void update_variables (string[] names) {
            bool changed = names.length != variables.length;
            for (int i = 0; !changed && i < names.length; i++) {
                changed = names[i] != variables[i];
            }
            if (!changed) return;

            foreach (Adw.PreferencesRow row in variable_rows) {
                variables_group.remove (row);
            }
            variable_rows = {};
            variables = names;

            foreach (unowned string variable in variables) {
                VariableItem? existing = window.data.get_variable_item (variable);
                if (existing != null) {
                    var row = new Adw.ActionRow () {
                        title = VariableBox.format_title (existing),
                        subtitle = _("Shared with other equations"),
                        use_markup = false
                    };
                    variables_group.add (row);
                    variable_rows += row;
                    continue;
                }

                unowned string? text = entered_values.lookup (variable);
                var row = new Adw.EntryRow () {
                    // Translators: Formatted with the name of a variable
                    title = _("%s =").printf (variable),
                    text = text == null ? MathTools.prettyprint_double (VariableItem.DEFAULT_VALUE) : text,
                    max_width_chars = 25,
                    activates_default = true,
                    use_markup = false
                };
                string name = variable;
                row.notify["text"].connect (() => {
                    entered_values.insert (name, row.get_text ());
                    update_validity ();
                });
                variables_group.add (row);
                variable_rows += row;
            }
            variables_group.set_visible (variables.length > 0);
            update_height ();
        }

        /**
         * Make room for the rows of the variables
         */
        private void update_height () {
            int minimum, natural;
            child.measure (
                Gtk.Orientation.VERTICAL, content_width, out minimum, out natural, null, null
            );
            set_content_height (natural);
        }

        private void update_validity () {
            bool variables_valid = true;
            bool equation_valid = MathTools.validate_parametric_equation (equation.get_text ());

            int index = 0;
            foreach (unowned string variable in variables) {
                Adw.PreferencesRow row = variable_rows[index++];
                double val;
                if (get_value (variable, out val)) {
                    row.remove_css_class ("error");
                } else {
                    row.add_css_class ("error");
                    variables_valid = false;
                }
            }

            if (equation_valid) {
                equation.remove_css_class ("error");
            } else {
                equation.add_css_class ("error");
            }
            confirm_button.set_sensitive (equation_valid && variables_valid);
        }

        [GtkCallback]
        private void on_equation_change () {
            try {
                unowned string text = equation.get_text ();
                expression_to_ast (text);
                update_variables (MathTools.get_free_variables (text));
            } catch (MathError e) {
                // Dont change the variables while the equation is being edited
            }
            update_validity ();
        }
    }
}
