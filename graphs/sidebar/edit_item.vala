// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/page.ui")]
    public class EditItemPage : Adw.NavigationPage {
        [GtkChild]
        private unowned Box edit_item_box { get; }

        public void load_item (Item item) {
            Widget widget;
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
            }

            edit_item_box.append (new EditItemFill (item));
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/base.ui")]
    public class EditItemBaseBox : Box {

        [GtkChild]
        private unowned Adw.EntryRow name_entry { get; }

        [GtkChild]
        private unowned Adw.ComboRow xposition { get; }

        [GtkChild]
        private unowned Adw.ComboRow yposition { get; }

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
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/data.ui")]
    public class EditItemDataItemBox : Box {

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
    public class EditItemErrorBarGroup : Box {

        [GtkChild]
        private unowned Adw.SwitchRow use_xerr { get; }

        [GtkChild]
        private unowned Adw.SwitchRow use_yerr { get; }

        [GtkChild]
        private unowned Adw.SwitchRow errbarsabove { get; }

        [GtkChild]
        private unowned StyleColorRow errcolor_row { get; }

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
            errcolor_row.notify["color"].connect ((obj, pspec) => {
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
                Expression ast = expression_to_ast (equation.get_text ());
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
                Expression ast = expression_to_ast (equation.get_text ());
                ast = PythonHelper.simplify_expression (ast);
                equation.set_text (ast_to_expression (ast));
                item.equation = ast;
            } catch (MathError e) {}
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/equation.ui")]
    public class EditItemEquationItemBox : Box {

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
    public class EditItemGeneratedDataItemBox : Box {

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
        private void on_entry_apply (Editable editable) {
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
    public class EditItemFill : Box {

        [GtkChild]
        private unowned Adw.SwitchRow fill_enabled { get; }

        [GtkChild]
        private unowned Adw.ComboRow fill_direction { get; }

        [GtkChild]
        private unowned Adw.ComboRow fill_item_row { get; }

        [GtkChild]
        private unowned StyleColorRow fill_color_row { get; }

        [GtkChild]
        private unowned Gtk.Scale fill_alpha_scale { get; }

        private Item item;
        private Gtk.SignalListItemFactory direction_factory;
        private Item[] reference_items = {};
        private uint[] reference_indices = {};
        private bool updating_references = false;

        public EditItemFill (Item item) {
            this.item = item;

            item.bind_property (
                "fillenabled",
                fill_enabled,
                "active",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "filldirection",
                fill_direction,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "fillalpha",
                fill_alpha_scale.adjustment,
                "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );

            string color = item.fillcolor == "" ? item.color : item.fillcolor;
            fill_color_row.color = Tools.hex_to_rgba (color);
            fill_color_row.notify["color"].connect (() => {
                item.fillcolor = Tools.rgba_to_hex (fill_color_row.color);
            });

            direction_factory = new Gtk.SignalListItemFactory ();
            direction_factory.setup.connect ((object) => {
                var list_item = (Gtk.ListItem) object;
                list_item.set_child (new Gtk.Label ("") { xalign = 0 });
            });
            direction_factory.bind.connect (on_direction_factory_bind);
            fill_direction.set_list_factory (direction_factory);

            fill_item_row.notify["selected"].connect (on_reference_change);
            map.connect (populate_reference_items);
        }

        private void populate_reference_items () {
            var window = get_root () as Window;
            if (window == null) return;

            updating_references = true;
            var names = new StringList (null);
            reference_items = {};
            reference_indices = {};
            bool found = false;
            uint selected = 0;
            uint index = 0;
            foreach (Item reference in window.data.get_items ()) {
                if (reference != item
                        && (reference is DataItem || reference is EquationItem)) {
                    if ((int) index == item.fillreference) {
                        found = true;
                        selected = names.get_n_items ();
                    }
                    names.append (reference.name);
                    reference_items += reference;
                    reference_indices += index;
                }
                index++;
            }
            fill_item_row.set_model (names);
            if (found) fill_item_row.set_selected (selected);
            updating_references = false;

            fill_direction.set_list_factory (null);
            fill_direction.set_list_factory (direction_factory);

            on_fill_direction ();
        }

        private void on_reference_change () {
            uint selected = fill_item_row.get_selected ();
            if (updating_references || selected == Gtk.INVALID_LIST_POSITION) return;
            if (selected >= reference_indices.length) return;
            item.fillreference = (int) reference_indices[selected];
        }

        private void on_direction_factory_bind (Object object) {
            var list_item = (Gtk.ListItem) object;
            var label = (Gtk.Label) list_item.get_child ();
            label.set_label (((Gtk.StringObject) list_item.get_item ()).get_string ());
            bool insensitive = list_item.get_position () == FillDirection.BETWEEN
                && reference_items.length == 0;
            list_item.set_selectable (!insensitive);
            list_item.set_activatable (!insensitive);
            label.set_sensitive (!insensitive);
        }

        [GtkCallback]
        private void on_fill_direction () {
            bool between = (FillDirection) fill_direction.get_selected () == FillDirection.BETWEEN;
            fill_item_row.set_visible (between && reference_items.length > 0);
            if (between && item.fillreference == -1 && reference_indices.length > 0) {
                item.fillreference = (int) reference_indices[fill_item_row.get_selected ()];
            }
        }
    }
}
