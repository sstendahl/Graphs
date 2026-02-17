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

        public void setup (Item item) {
            this.item = item;

            Value text = Value (typeof (string));
            item.get_property ("equation", ref text);

            equation.set_text (text.get_string ());
            equation.changed.connect (on_equation_change);
        }

        private void on_equation_change () {
            string text = equation.get_text ();
            if (PythonHelper.validate_equation (text)) {
                equation.remove_css_class ("error");
                Value val = Value (typeof (string));
                val.set_string (text);
                item.set_property ("equation", val);
            } else {
                equation.add_css_class ("error");
            }
        }

        [GtkCallback]
        private void on_simplify () {
            try {
                string equation_str = equation.get_text ();
                equation_str = preprocess_equation (equation_str);
                equation_str = PythonHelper.simplify_equation (equation_str);
                equation_str = prettify_equation (equation_str);

                equation.set_text (equation_str);
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

            xstart.changed.connect (on_entry_change);
            xstop.changed.connect (on_entry_change);

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

        private void on_entry_change (Editable entry) {
            string text = entry.get_text ();
            string prop = entry.get_buildable_id ();
            if (try_evaluate_string (text)) {
                entry.remove_css_class ("error");
                Value val = Value (typeof (string));
                val.set_string (text);
                item.set_property (prop, val);
            } else {
                entry.add_css_class ("error");
            }
        }
    }
}
