// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/equation-group.ui")]
    public class EditItemEquationGroup : Adw.PreferencesGroup {
        [GtkChild]
        private unowned Adw.EntryRow equation { get; }
        [GtkChild]
        private unowned Adw.ButtonRow simplify { get; }

        private EquationBasedItem item;

        public void setup (EquationBasedItem item) {
            this.item = item;
            try {
                equation.set_text (ast_to_expression (item.equation));
            } catch (MathError e) { assert_not_reached (); }
        }

        [GtkCallback]
        private void on_equation_change () {
            if (MathTools.validate_equation (equation.get_text ())) {
                equation.remove_css_class ("error");
                equation.set_show_apply_button (true);
            } else {
                equation.add_css_class ("error");
                equation.set_show_apply_button (false);
            }
        }

        [GtkCallback]
        private void on_equation_apply () {
            try {
                Ast ast = expression_to_ast (equation.get_text ());
                equation.set_text (ast_to_expression (ast));
                item.equation = ast;
            } catch (MathError e) { assert_not_reached (); }

            // workaround button not disappearing when pressed
            equation.set_show_apply_button (false);
            equation.set_show_apply_button (true);
        }

        [GtkCallback]
        private void on_simplify () {
            try {
                Ast ast = expression_to_ast (equation.get_text ());
                ast = PythonHelper.simplify_expression (ast);
                equation.set_text (ast_to_expression (ast));
                item.equation = ast;
            } catch (MathError e) {}
        }
    }
}
