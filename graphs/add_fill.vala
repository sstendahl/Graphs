// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/add-fill.ui")]
    public class AddFillDialog : Adw.Dialog {
        [GtkChild]
        private unowned Adw.ToggleGroup upper_type { get; }
        [GtkChild]
        private unowned Adw.ComboRow upper_item { get; }
        [GtkChild]
        private unowned Adw.EntryRow upper_equation { get; }
        [GtkChild]
        private unowned Adw.ToggleGroup lower_type { get; }
        [GtkChild]
        private unowned Adw.ComboRow lower_item { get; }
        [GtkChild]
        private unowned Adw.EntryRow lower_equation { get; }
        [GtkChild]
        private unowned Adw.EntryRow item_name { get; }
        [GtkChild]
        private unowned Gtk.Button confirm_button { get; }

        private const uint TYPE_ITEM = 0;
        private const uint TYPE_EQUATION = 1;

        private Window window;
        private Settings settings;
        private Item[] source_items;
        private bool ready = false;

        public AddFillDialog (Window window) {
            Object ();
            this.window = window;
            this.settings = Application.get_settings_child ("add-fill");

            var names = new Gtk.StringList (null);
            var items = new Gee.ArrayList<Item> ();
            foreach (var item in window.data) {
                if (item is DataItem || item is EquationItem) {
                    names.append (item.name);
                    items.add (item);
                }
            }
            this.source_items = items.to_array ();
            upper_item.set_model (names);
            lower_item.set_model (names);

            upper_equation.set_text (settings.get_string ("upper-equation"));
            lower_equation.set_text (settings.get_string ("lower-equation"));

            if (source_items.length > 1) {
                lower_item.set_selected (1);
            } else {
                lower_type.set_active (TYPE_EQUATION);
            }

            ready = true;
            update_state ();
            present (window);
        }

        private bool is_equation_valid (Adw.EntryRow equation) {
            return MathTools.validate_equation (equation.get_text ());
        }

        private void update_bound_rows (
            Adw.ToggleGroup type, Adw.ComboRow combo, Adw.EntryRow equation
        ) {
            bool is_equation = type.get_active () == TYPE_EQUATION;
            combo.set_visible (!is_equation);
            equation.set_visible (is_equation);

            if (is_equation && !is_equation_valid (equation)) {
                equation.add_css_class ("error");
            } else {
                equation.remove_css_class ("error");
            }
        }

        private void set_equation_enabled (Adw.ToggleGroup type, bool enabled) {
            type.get_toggle (TYPE_EQUATION).set_enabled (enabled);
        }

        private void update_state () {
            if (!ready) return;
            ready = false;

            update_bound_rows (upper_type, upper_item, upper_equation);
            update_bound_rows (lower_type, lower_item, lower_equation);

            bool upper_is_item = upper_type.get_active () == TYPE_ITEM;
            bool lower_is_item = lower_type.get_active () == TYPE_ITEM;
            set_equation_enabled (lower_type, upper_is_item);
            set_equation_enabled (upper_type, lower_is_item);

            ready = true;

            bool valid = source_items.length > 0
                && (upper_is_item || is_equation_valid (upper_equation))
                && (lower_is_item || is_equation_valid (lower_equation));
            confirm_button.set_sensitive (valid);
        }

        [GtkCallback]
        private void on_type_change () {
            update_state ();
        }

        [GtkCallback]
        private void on_input_change () {
            update_state ();
        }

        private void apply_bound (
            FillItem fill, Adw.ToggleGroup type, Adw.ComboRow combo,
            Adw.EntryRow equation, bool is_upper
        ) {
            if (type.get_active () == TYPE_EQUATION) {
                try {
                    Ast ast = expression_to_ast (equation.get_text ());
                    if (is_upper) fill.set_upper_equation (ast);
                    else fill.set_lower_equation (ast);
                } catch (MathError e) { assert_not_reached (); }
            } else {
                Item source = source_items[combo.get_selected ()];
                if (is_upper) fill.set_upper_source (source);
                else fill.set_lower_source (source);
            }
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
            apply_bound (fill, upper_type, upper_item, upper_equation, true);
            apply_bound (fill, lower_type, lower_item, lower_equation, false);

            unowned string name = item_name.get_text ();
            item.name = name == "" ? _("Fill") : name;

            Item[] items = {item};
            window.data.add_items (items);
            window.data.optimize_limits ();
            close ();
        }
    }
}
