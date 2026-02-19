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
            string typename = item.get_type ().name ();

            if (typename == "GraphsGeneratedDataItem") {
                edit_item_box.append (new EditItemGeneratedDataItemBox (item));
            }
            if (typename == "GraphsDataItem" || typename == "GraphsGeneratedDataItem") {
                edit_item_box.append (new EditItemDataItemBox (item));
                bool has_xerr, has_yerr;
                PythonHelper.item_has_err (item, out has_xerr, out has_yerr);
                if (has_xerr || has_yerr) {
                    edit_item_box.append (new EditItemErrorBarGroup (item));
                }
            } else if (typename == "GraphsEquationItem") {
                edit_item_box.append (new EditItemEquationItemBox (item));
            }
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
        private unowned Scale errcapsize { get; }

        [GtkChild]
        private unowned Scale errcapthick { get; }

        [GtkChild]
        private unowned Scale errlinewidth { get; }

        private Item item;

        public EditItemErrorBarGroup (Item item) {
            this.item = item;

            bool has_xerr, has_yerr;
            PythonHelper.item_has_err (item, out has_xerr, out has_yerr);

            use_xerr.set_visible (has_xerr);
            use_yerr.set_visible (has_yerr);

            if (has_xerr) {
                item.bind_property (
                    "showxerr",
                    use_xerr,
                    "active",
                    BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
                );
            }
            if (has_yerr) {
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

            string current_errcolor;
            item.get ("errcolor", out current_errcolor);
            errcolor_row.color = Tools.hex_to_rgba (current_errcolor);
            errcolor_row.notify["color"].connect ((obj, pspec) => {
                item.set ("errcolor", Tools.rgba_to_hex (errcolor_row.color));
            });
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/equation-group.ui")]
    public class EditItemEquationGroup : Adw.PreferencesGroup {

        [GtkChild]
        private unowned Adw.EntryRow equation { get; }

        [GtkChild]
        private unowned Adw.ButtonRow simplify { get; }

        private Item item;

        public void setup (Item item) {
            this.item = item;

            string text;
            item.get ("equation", out text);
            equation.set_text (text);
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
            item.set ("equation", equation.get_text ());
        }

        [GtkCallback]
        private void on_simplify () {
            try {
                string equation_str = equation.get_text ();
                equation_str = preprocess_equation (equation_str);
                equation_str = PythonHelper.simplify_equation (equation_str);
                equation_str = prettify_equation (equation_str);

                equation.set_text (equation_str);
                item.set ("equation", equation_str);
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

        private Item item;

        public EditItemGeneratedDataItemBox (Item item) {
            this.item = item;
            equation_group.setup (item);

            string text;
            item.get ("xstart", out text);
            xstart.set_text (text);
            item.get ("xstop", out text);
            xstop.set_text (text);

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
}
