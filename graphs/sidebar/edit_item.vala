// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/page.ui")]
    public class EditItemPage : Adw.NavigationPage {
        [GtkChild]
        private unowned Gtk.Box edit_item_box { get; }

        public void load_item (Item item) {
            Gtk.Widget widget;
            while ((widget = edit_item_box.get_last_child ()) != null) {
                edit_item_box.remove (widget);
            }

            edit_item_box.append (new EditItemBaseBox (item));

            if (item is GeneratedDataItem) {
                edit_item_box.append (new EditItemGeneratedDataItemBox ((GeneratedDataItem) item));
            }
            if (item is DataItem) {
                DataItem data_item = (DataItem) item;
                edit_item_box.append (new EditItemDataItemBox (data_item));
                if (data_item.has_xerr () || data_item.has_yerr ()) {
                    edit_item_box.append (new EditItemErrorBarGroup (data_item));
                }
            } else if (item is EquationItem) {
                edit_item_box.append (new EditItemEquationItemBox ((EquationItem) item));
            } else if (item is FillItem) {
                var window = (Window) get_root ();
                edit_item_box.append (new EditItemFillItemBox ((FillItem) item, window.data));
            }
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/base.ui")]
    public class EditItemBaseBox : Gtk.Box {

        [GtkChild]
        private unowned Adw.EntryRow name_entry { get; }

        [GtkChild]
        private unowned Adw.ComboRow xposition { get; }

        [GtkChild]
        private unowned Adw.ComboRow yposition { get; }

        [GtkChild]
        private unowned Adw.SwitchRow legend { get; }

        public EditItemBaseBox (Item item) {
            item.bind_property (
                "name",
                name_entry,
                "text",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "xposition",
                xposition,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "yposition",
                yposition,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            if (item is LegendableItem) {
                item.bind_property (
                    "legend",
                    legend,
                    "active",
                    BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
                );
                legend.visible = true;
            }
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/data.ui")]
    public class EditItemDataItemBox : Gtk.Box {

        [GtkChild]
        private unowned Adw.ComboRow linestyle { get; }

        [GtkChild]
        private unowned Gtk.Scale linewidth { get; }

        [GtkChild]
        private unowned Adw.ComboRow markerstyle { get; }

        [GtkChild]
        private unowned Gtk.Scale markersize { get; }

        public EditItemDataItemBox (DataItem item) {
            item.bind_property (
                "linestyle",
                linestyle,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "linewidth",
                linewidth.adjustment,
                "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "markerstyle",
                markerstyle,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "markersize",
                markersize.adjustment,
                "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
        }

        [GtkCallback]
        private void on_linestyle () {
            linewidth.set_sensitive (linestyle.get_selected () != 0);
        }

        [GtkCallback]
        private void on_markers () {
            markersize.set_sensitive (markerstyle.get_selected () != 0);
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/errorbar-group.ui")]
    public class EditItemErrorBarGroup : Gtk.Box {

        [GtkChild]
        private unowned Adw.SwitchRow use_xerr { get; }

        [GtkChild]
        private unowned Adw.SwitchRow use_yerr { get; }

        [GtkChild]
        private unowned Adw.SwitchRow errbarsabove { get; }

        [GtkChild]
        private unowned ColorRow errcolor_row { get; }

        [GtkChild]
        private unowned Gtk.Scale errcapsize { get; }

        [GtkChild]
        private unowned Gtk.Scale errcapthick { get; }

        [GtkChild]
        private unowned Gtk.Scale errlinewidth { get; }

        public EditItemErrorBarGroup (DataItem item) {
            if (item.has_xerr ()) {
                use_xerr.set_visible (true);
                item.bind_property (
                    "showxerr",
                    use_xerr,
                    "active",
                    BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
                );
            }
            if (item.has_yerr ()) {
                use_yerr.set_visible (true);
                item.bind_property (
                    "showyerr",
                    use_yerr,
                    "active",
                    BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
                );
            }

            item.bind_property (
                "errbarsabove", errbarsabove, "active",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "errcapsize", errcapsize.adjustment, "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "errcapthick", errcapthick.adjustment, "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "errlinewidth", errlinewidth.adjustment, "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );

            errcolor_row.color = Tools.hex_to_rgba (item.errcolor);
            errcolor_row.color_chosen.connect (() => {
                item.errcolor = Tools.rgba_to_hex (errcolor_row.color);
            });
        }
    }

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

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/equation.ui")]
    public class EditItemEquationItemBox : Gtk.Box {

        [GtkChild]
        private unowned EditItemEquationGroup equation_group { get; }

        [GtkChild]
        private unowned Adw.ComboRow linestyle { get; }

        [GtkChild]
        private unowned Gtk.Scale linewidth { get; }

        public EditItemEquationItemBox (EquationItem item) {
            equation_group.setup (item);
            item.bind_property (
                "linestyle",
                linestyle,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "linewidth",
                linewidth.adjustment,
                "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
        }
    }

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

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/fill.ui")]
    public class EditItemFillItemBox : Gtk.Box {

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
        private unowned Gtk.Scale alpha { get; }

        private const uint TYPE_ITEM = 0;
        private const uint TYPE_EQUATION = 1;

        private FillItem item;
        private Settings settings;
        private Item[] source_items;
        private bool ready = false;

        public EditItemFillItemBox (FillItem item, Data data) {
            this.item = item;
            this.settings = Application.get_settings_child ("add-fill");

            var names = new Gtk.StringList (null);
            var items = new Gee.ArrayList<Item> ();
            foreach (var it in data) {
                if (it is DataItem || it is EquationItem) {
                    names.append (it.name);
                    items.add (it);
                }
            }
            this.source_items = items.to_array ();
            upper_item.set_model (names);
            lower_item.set_model (names);

            init_bound (
                item.get_upper_kind (), item.get_upper_source (),
                item.get_upper_equation (),
                upper_type, upper_item, upper_equation, "upper-equation"
            );
            init_bound (
                item.get_lower_kind (), item.get_lower_source (),
                item.get_lower_equation (),
                lower_type, lower_item, lower_equation, "lower-equation"
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

        private int index_of (Item? target) {
            if (target == null) return -1;
            for (int i = 0; i < source_items.length; i++) {
                if (source_items[i] == target) return i;
            }
            return -1;
        }

        private void init_bound (
            FillBoundKind kind, Item? source_item, Ast? equation,
            Adw.ToggleGroup type, Adw.ComboRow item_combo,
            Adw.EntryRow equation_row, string settings_key
        ) {
            equation_row.set_text (settings.get_string (settings_key));

            if (kind == FillBoundKind.ITEM) {
                type.set_active (TYPE_ITEM);
                int index = index_of (source_item);
                if (index < 0) {
                    item_combo.set_sensitive (false);
                    return;
                }
                item_combo.set_selected (index);
            } else {
                type.set_active (TYPE_EQUATION);
                if (equation != null) {
                    try {
                        equation_row.set_text (ast_to_expression (equation));
                    } catch (MathError e) {}
                }
            }
        }

        private bool is_equation_valid (Adw.EntryRow equation_row) {
            return MathTools.validate_equation (equation_row.get_text ());
        }

        private void update_bound_rows (
            Adw.ToggleGroup type, Adw.ComboRow combo, Adw.EntryRow equation_row
        ) {
            bool is_equation = type.get_active () == TYPE_EQUATION;
            combo.set_visible (!is_equation);
            equation_row.set_visible (is_equation);

            if (is_equation && !is_equation_valid (equation_row)) {
                equation_row.add_css_class ("error");
            } else {
                equation_row.remove_css_class ("error");
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

            set_equation_enabled (
                lower_type, upper_type.get_active () == TYPE_ITEM
            );
            set_equation_enabled (
                upper_type, lower_type.get_active () == TYPE_ITEM
            );

            ready = true;
        }

        private void apply_bound (
            Adw.ToggleGroup type, Adw.ComboRow combo,
            Adw.EntryRow equation_row, bool is_upper
        ) {
            if (type.get_active () == TYPE_EQUATION) {
                if (!is_equation_valid (equation_row)) return;
                try {
                    Ast ast = expression_to_ast (equation_row.get_text ());
                    if (is_upper) item.set_upper_equation (ast);
                    else item.set_lower_equation (ast);
                } catch (MathError e) { assert_not_reached (); }
            } else if (combo.get_selected () < source_items.length) {
                Item source = source_items[combo.get_selected ()];
                if (is_upper) item.set_upper_source (source);
                else item.set_lower_source (source);
            }
        }

        [GtkCallback]
        private void on_upper_change () {
            if (!ready) return;
            update_state ();
            apply_bound (upper_type, upper_item, upper_equation, true);
        }

        [GtkCallback]
        private void on_lower_change () {
            if (!ready) return;
            update_state ();
            apply_bound (lower_type, lower_item, lower_equation, false);
        }
    }
}
