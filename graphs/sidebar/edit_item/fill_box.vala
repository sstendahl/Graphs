// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/fill.ui")]
    public class EditItemFillItemBox : Gtk.Box {
        [GtkChild]
        private unowned Adw.ComboRow upper_bound { get; }
        [GtkChild]
        private unowned Adw.EntryRow upper_equation { get; }
        [GtkChild]
        private unowned Adw.ComboRow lower_bound { get; }
        [GtkChild]
        private unowned Adw.EntryRow lower_equation { get; }
        [GtkChild]
        private unowned Gtk.Scale alpha { get; }

        private FillItem item;
        private Settings settings;
        private Item[] source_items;
        private bool ready = false;

        public EditItemFillItemBox (FillItem item, Data data) {
            this.item = item;
            this.settings = Application.get_settings_child ("add-fill");

            this.source_items = FillBounds.get_source_items (data);
            upper_bound.set_model (FillBounds.create_model (source_items));
            lower_bound.set_model (FillBounds.create_model (source_items));

            init_bound (
                item.get_upper_kind (), item.get_upper_source (),
                item.get_upper_equation (),
                upper_bound, upper_equation, "upper-equation"
            );
            init_bound (
                item.get_lower_kind (), item.get_lower_source (),
                item.get_lower_equation (),
                lower_bound, lower_equation, "lower-equation"
            );

            item.bind_property (
                "alpha",
                alpha.adjustment,
                "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );

            ready = true;
            update_state ();
        }

        private void init_bound (
            FillBoundKind kind, Item? source_item, Ast? equation,
            Adw.ComboRow combo, Adw.EntryRow equation_row, string settings_key
        ) {
            equation_row.set_text (settings.get_string (settings_key));

            uint selected = FillBounds.get_selection (
                kind, source_item, equation, source_items
            );
            combo.set_selected (selected);
        }

        private bool is_equation_valid (Adw.EntryRow equation_row) {
            return MathTools.validate_equation (equation_row.get_text ());
        }

        private void update_bound_rows (
            Adw.ComboRow combo, Adw.EntryRow equation_row
        ) {
            bool is_custom = combo.get_selected () == FillBoundSelection.CUSTOM;
            equation_row.set_sensitive (is_custom);

            if (is_custom && !is_equation_valid (equation_row)) {
                equation_row.add_css_class ("error");
            } else {
                equation_row.remove_css_class ("error");
            }
        }

        private void update_state () {
            if (!ready) return;

            update_bound_rows (upper_bound, upper_equation);
            update_bound_rows (lower_bound, lower_equation);
        }

        private void apply_bound (
            Adw.ComboRow combo, Adw.EntryRow equation_row, bool is_upper
        ) {
            uint selected = combo.get_selected ();

            if (selected >= FillBoundSelection.TOP_ITEM) {
                uint index = selected - FillBoundSelection.TOP_ITEM;
                Item source = source_items[index];
                if (is_upper) item.set_upper_source (source);
                else item.set_lower_source (source);
                return;
            }

            string? expression = FillBounds.get_expression (
                (FillBoundSelection) selected
            );
            if (expression == null) {
                if (!is_equation_valid (equation_row)) return;
                expression = equation_row.get_text ();
            }
            try {
                Ast ast = expression_to_ast (expression);
                if (is_upper) item.set_upper_equation (ast);
                else item.set_lower_equation (ast);
            } catch (MathError e) { assert_not_reached (); }
        }

        [GtkCallback]
        private void on_upper_change () {
            if (!ready) return;
            update_state ();
            apply_bound (upper_bound, upper_equation, true);
        }

        [GtkCallback]
        private void on_lower_change () {
            if (!ready) return;
            update_state ();
            apply_bound (lower_bound, lower_equation, false);
        }
    }
}
