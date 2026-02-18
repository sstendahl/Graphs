// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item.ui")]
    public class EditItemPage : Adw.NavigationPage {
        [GtkChild]
        private unowned Box edit_item_box { get; }

        public void load_item (Item item) {
            Widget widget;
            while ((widget = edit_item_box.get_last_child ()) != null) {
                edit_item_box.remove (widget);
            }

            edit_item_box.append (new EditItemBaseBox (item));
            string typename = item.get_type ().name ();

            if (typename == "GraphsGeneratedDataItem") {
                edit_item_box.append (new EditItemGeneratedDataItemBox (item));
            }
            if (typename == "GraphsDataItem" || typename == "GraphsGeneratedDataItem") {
                edit_item_box.append (new EditItemDataItemBox (item));
            } else if (typename == "GraphsEquationItem") {
                edit_item_box.append (new EditItemEquationItemBox (item));
            }
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/edit-item/base.ui")]
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

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/edit-item/data.ui")]
    public class EditItemDataItemBox : Box {

        [GtkChild]
        private unowned Adw.ComboRow linestyle { get; }

        [GtkChild]
        private unowned Scale linewidth { get; }

        [GtkChild]
        private unowned Adw.ComboRow markerstyle { get; }

        [GtkChild]
        private unowned Scale markersize { get; }

        public EditItemDataItemBox (Item item) {
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

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/edit-item/equation-group.ui")]
    public class EditItemEquationGroup : Adw.PreferencesGroup {

        [GtkChild]
        private unowned Adw.EntryRow equation { get; }

        [GtkChild]
        private unowned Adw.ButtonRow simplify { get; }

        private Item item;
        private Value val;

        public void setup (Item item) {
            this.item = item;
            this.val = Value (typeof (string));

            item.get_property ("equation", ref val);
            equation.set_text (val.get_string ());
        }

        [GtkCallback]
        private void on_equation_change () {
            if (PythonHelper.validate_equation (equation.get_text ())) {
                equation.remove_css_class ("error");
                equation.set_show_apply_button (true);
            } else {
                equation.add_css_class ("error");
                equation.set_show_apply_button (false);
            }
        }

        [GtkCallback]
        private void on_equation_apply () {
            val.set_string (equation.get_text ());
            item.set_property ("equation", val);
        }

        [GtkCallback]
        private void on_simplify () {
            try {
                string equation_str = equation.get_text ();
                equation_str = preprocess_equation (equation_str);
                equation_str = PythonHelper.simplify_equation (equation_str);
                equation_str = prettify_equation (equation_str);

                equation.set_text (equation_str);
                val.set_string (equation_str);
                item.set_property ("equation", val);
            } catch (MathError e) {}
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/edit-item/equation.ui")]
    public class EditItemEquationItemBox : Box {

        [GtkChild]
        private unowned EditItemEquationGroup equation_group { get; }

        [GtkChild]
        private unowned Adw.ComboRow linestyle { get; }

        [GtkChild]
        private unowned Scale linewidth { get; }

        public EditItemEquationItemBox (Item item) {
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

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/edit-item/generated-data.ui")]
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

        private Item item;

        public EditItemGeneratedDataItemBox (Item item) {
            this.item = item;
            equation_group.setup (item);

            Value text = Value (typeof (string));
            item.get_property ("xstart", ref text);
            xstart.set_text (text.get_string ());
            item.get_property ("xstop", ref text);
            xstop.set_text (text.get_string ());

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
            Value val = Value (typeof (string));
            val.set_string (editable.get_text ());
            item.set_property (editable.get_buildable_id (), val);
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
