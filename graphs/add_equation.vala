// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Add Equation dialog.
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/add-equation.ui")]
    public class AddEquationDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.EntryRow equation { get; }

        [GtkChild]
        private unowned Button confirm_button { get; }

        [GtkChild]
        private unowned Adw.EntryRow item_name { get; }

        private Window window;
        private GLib.Settings settings;

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
                Expression expression = expression_to_ast (equation_str);

                Item item = ItemFactory.new_equation_item (window.data.selected_style_params, expression);
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
                confirm_button.set_sensitive (true);
            } else {
                equation.add_css_class ("error");
                confirm_button.set_sensitive (false);
            }
        }
    }
}
