// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/add-fill.ui")]
    public class AddFillDialog : Adw.Dialog {
        [GtkChild]
        private unowned Adw.ComboRow upper_bound { get; }
        [GtkChild]
        private unowned Adw.EntryRow upper_equation { get; }
        [GtkChild]
        private unowned Adw.ComboRow lower_bound { get; }
        [GtkChild]
        private unowned Adw.EntryRow lower_equation { get; }
        [GtkChild]
        private unowned Adw.EntryRow item_name { get; }
        [GtkChild]
        private unowned Gtk.Button confirm_button { get; }

        private Window window;
        private Settings settings;
        private Item[] source_items;
        private bool ready = false;

        public AddFillDialog (Window window) {
            Object ();
            this.window = window;
            this.settings = Application.get_settings_child ("add-fill");

            this.source_items = FillBounds.get_source_items (window.data);
            upper_bound.set_model (FillBounds.create_model (source_items));
            lower_bound.set_model (FillBounds.create_model (source_items));

            upper_equation.set_text (settings.get_string ("upper-equation"));
            lower_equation.set_text (settings.get_string ("lower-equation"));

            upper_bound.set_selected (
                source_items.length > 0
                    ? FillBoundSelection.TOP_ITEM : FillBoundSelection.CUSTOM
            );
            lower_bound.set_selected (FillBoundSelection.NEG_INF);

            ready = true;
            update_state ();
            present (window);
        }

        private bool is_equation_valid (Adw.EntryRow equation) {
            return MathTools.validate_equation (equation.get_text ());
        }

        private bool is_bound_valid (
            Adw.ComboRow combo, Adw.EntryRow equation
        ) {
            if (combo.get_selected () != FillBoundSelection.CUSTOM) return true;
            return is_equation_valid (equation);
        }

        private void update_bound_rows (
            Adw.ComboRow combo, Adw.EntryRow equation
        ) {
            bool is_custom = combo.get_selected () == FillBoundSelection.CUSTOM;
            equation.set_sensitive (is_custom);

            if (is_custom && !is_equation_valid (equation)) {
                equation.add_css_class ("error");
            } else {
                equation.remove_css_class ("error");
            }
        }

        private void update_state () {
            if (!ready) return;

            update_bound_rows (upper_bound, upper_equation);
            update_bound_rows (lower_bound, lower_equation);

            confirm_button.set_sensitive (
                is_bound_valid (upper_bound, upper_equation)
                && is_bound_valid (lower_bound, lower_equation)
            );
        }

        [GtkCallback]
        private void on_upper_change () {
            update_state ();
        }

        [GtkCallback]
        private void on_lower_change () {
            update_state ();
        }

        private void apply_bound (
            FillItem fill, Adw.ComboRow combo, Adw.EntryRow equation,
            bool is_upper
        ) {
            uint selected = combo.get_selected ();

            if (selected >= FillBoundSelection.TOP_ITEM) {
                Item source = source_items[selected - FillBoundSelection.TOP_ITEM];
                if (is_upper) fill.set_upper_source (source);
                else fill.set_lower_source (source);
                return;
            }

            string expression =
                FillBounds.get_expression ((FillBoundSelection) selected)
                ?? equation.get_text ();
            try {
                Ast ast = expression_to_ast (expression);
                if (is_upper) fill.set_upper_equation (ast);
                else fill.set_lower_equation (ast);
            } catch (MathError e) { assert_not_reached (); }
        }

        [GtkCallback]
        private void on_accept () {
            settings.set_string ("upper-equation", upper_equation.get_text ());
            settings.set_string ("lower-equation", lower_equation.get_text ());

            var item = ItemFactory.new_fill_item (
                window.data.selected_style_params,
                new double[0], new double[0], new double[0]
            );
            var fill = (FillItem) item;
            apply_bound (fill, upper_bound, upper_equation, true);
            apply_bound (fill, lower_bound, lower_equation, false);

            unowned string name = item_name.get_text ();
            item.name = name == "" ? _("Fill") : name;

            Item[] items = {item};
            window.data.add_items (items);
            window.data.optimize_limits ();
            close ();
        }
    }
}
