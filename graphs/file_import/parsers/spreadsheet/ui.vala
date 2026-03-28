using Gtk;
using Gee;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/spreadsheet/main-group.ui")]
    public class SpreadsheetGroup : Adw.PreferencesGroup {
        [GtkChild]
        private unowned Adw.ComboRow sheet_selector;

        public SpreadsheetGroup (ImportSettings settings) {
            var string_list = (Gtk.StringList) settings.get_item ("sheet-names");
            sheet_selector.set_model (string_list);
            sheet_selector.set_selected (settings.get_int ("sheet-index"));

            sheet_selector.notify["selected"].connect (() => {
                settings.set_int ("sheet-index", (int) sheet_selector.get_selected ());
            });
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/spreadsheet/item-group.ui")]
    public class SpreadsheetItemGroup : Adw.PreferencesGroup {
        [GtkChild]
        private unowned Adw.SpinRow column_x { get; }
        [GtkChild]
        private unowned Adw.SpinRow column_y { get; }
        [GtkChild]
        private unowned Adw.SwitchRow single_column { get; }
        [GtkChild]
        private unowned Adw.EntryRow equation { get; }
        [GtkChild]
        private unowned Adw.SwitchRow use_xerr { get; }
        [GtkChild]
        private unowned Adw.SwitchRow use_yerr { get; }
        [GtkChild]
        private unowned Adw.SpinRow column_xerr { get; }
        [GtkChild]
        private unowned Adw.SpinRow column_yerr { get; }
        [GtkChild]
        private unowned Button remove_button { get; }

        public signal void settings_changed (ColumnsItemSettings new_settings);
        public signal void remove_request ();

        public SpreadsheetItemGroup (ColumnsItemSettings item_settings, bool removable) {
            remove_button.set_visible (removable);

            column_x.output.connect (on_output);
            column_x.input.connect (on_input);
            column_y.output.connect (on_output);
            column_y.input.connect (on_input);
            column_xerr.output.connect (on_output);
            column_xerr.input.connect (on_input);
            column_yerr.output.connect (on_output);
            column_yerr.input.connect (on_input);

            load_item_settings (item_settings);

            single_column.notify["active"].connect (on_settings_changed);
            column_x.notify["value"].connect (on_settings_changed);
            column_y.notify["value"].connect (on_settings_changed);
            equation.notify["text"].connect (on_settings_changed);
            use_xerr.notify["active"].connect (on_settings_changed);
            use_yerr.notify["active"].connect (on_settings_changed);
            column_xerr.notify["value"].connect (on_settings_changed);
            column_yerr.notify["value"].connect (on_settings_changed);
        }

        private void load_item_settings (ColumnsItemSettings item_settings) {
            column_x.set_value (item_settings.column_x);
            column_y.set_value (item_settings.column_y);
            single_column.set_active (item_settings.single_column);
            equation.set_text (item_settings.equation);
            use_xerr.set_active (item_settings.use_xerr);
            use_yerr.set_active (item_settings.use_yerr);
            column_xerr.set_value (item_settings.xerr_index);
            column_yerr.set_value (item_settings.yerr_index);
        }

        private ColumnsItemSettings get_item_settings () {
            var item_settings = ColumnsItemSettings ();
            item_settings.column_x = (int) column_x.get_value ();
            item_settings.column_y = (int) column_y.get_value ();
            item_settings.single_column = single_column.get_active ();
            item_settings.equation = equation.get_text ().replace (";", "");
            item_settings.use_xerr = use_xerr.get_active ();
            item_settings.use_yerr = use_yerr.get_active ();
            item_settings.xerr_index = (int) column_xerr.get_value ();
            item_settings.yerr_index = (int) column_yerr.get_value ();
            return item_settings;
        }

        private void on_settings_changed () {
            settings_changed.emit (get_item_settings ());
        }

        [GtkCallback]
        private void on_remove () {
            remove_request.emit ();
        }

        private bool on_output (Adw.SpinRow spin_button) {
            spin_button.set_text (Tools.int_to_alpha ((int) spin_button.get_value ()));
            return true;
        }

        private int on_input (Adw.SpinRow spin_button, out double new_value) {
            new_value = Tools.alpha_to_int (spin_button.get_text ().strip ().up ());
            return 1;
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/spreadsheet/box.ui")]
    public class SpreadsheetBox : Box {
        [GtkChild]
        private unowned Box items_box { get; }

        private ImportSettings settings;
        private Gee.List<ColumnsItemSettings?> items;

        public SpreadsheetBox (ImportSettings settings) {
            this.settings = settings;

            var iter = settings.get_value ("items").iterator ();
            size_t n_items = iter.n_children ();
            ColumnsItemSettings?[] item_settings_list = new ColumnsItemSettings?[n_items];
            for (int i = 0; i < n_items; i++) {
                item_settings_list[i] = ColumnsItemSettings ();
                item_settings_list[i].load_from_variant (iter.next_value ());
            }
            items = new ArrayList<ColumnsItemSettings?>.wrap (item_settings_list);

            reload_item_groups ();
        }

        private void reload_item_groups () {
            Widget widget;
            while ((widget = items_box.get_last_child ()) != null) {
                items_box.remove (widget);
            }

            for (int i = 0; i < items.size; i++) {
                int index = i;

                var item_group = new SpreadsheetItemGroup (items[i], i > 0);
                item_group.set_title (_("Item %d").printf (i + 1));

                item_group.settings_changed.connect ((new_settings) => {
                    items[index] = new_settings;
                    update_settings ();
                });

                item_group.remove_request.connect (() => {
                    items.remove_at (index);
                    update_settings ();
                    reload_item_groups ();
                });

                items_box.append (item_group);
            }
        }

        [GtkCallback]
        private void add () {
            var new_settings = ColumnsItemSettings ();
            new_settings.load_from_variant (items[0].to_variant ());
            items.add (new_settings);
            update_settings ();
            reload_item_groups ();
        }

        private void update_settings () {
            var builder = new VariantBuilder (new VariantType ("a(iiiibbbs)"));
            foreach (var item_settings in items) {
                builder.add_value (item_settings.to_variant ());
            }
            settings.set_value ("items", builder.end ());
        }
    }
}
