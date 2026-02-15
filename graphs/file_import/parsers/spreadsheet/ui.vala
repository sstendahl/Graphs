using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/spreadsheet/main-group.ui")]
    public class SpreadsheetGroup : Adw.PreferencesGroup {
        [GtkChild]
        private unowned Adw.ComboRow sheet_selector;

        [GtkChild]
        private unowned Adw.ComboRow separator;

        public SpreadsheetGroup (ImportSettings settings) {
            var string_list = settings.get_item ("sheet-names") as Gtk.StringList;
            sheet_selector.set_model (string_list);
            sheet_selector.set_selected (settings.get_int ("sheet-index"));

            separator.set_selected (ColumnsSeparator.parse (settings.get_string ("separator")));

            separator.notify["selected"].connect (() => {
                settings.set_string ("separator", ((ColumnsSeparator) separator.get_selected ()).friendly_string ());
            });

            sheet_selector.notify["selected"].connect (() => {
                settings.set_int ("sheet-index", (int) sheet_selector.get_selected ());
            });
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/spreadsheet/item-group.ui")]
    public class SpreadsheetItemGroup : Adw.PreferencesGroup {
        [GtkChild]
        public unowned Adw.SpinRow column_x { get; }
        [GtkChild]
        public unowned Adw.SpinRow column_y { get; }
        [GtkChild]
        public unowned Adw.SwitchRow single_column { get; }
        [GtkChild]
        public unowned Adw.EntryRow equation { get; }
        [GtkChild]
        public unowned Button remove_button { get; }

        public signal void settings_changed (ColumnsItemSettings new_settings);
        public signal void remove_request ();

        public SpreadsheetItemGroup (ColumnsItemSettings item_settings, bool removable) {
            remove_button.set_visible (removable);

            column_x.output.connect (on_output);
            column_x.input.connect (on_input);
            column_y.output.connect (on_output);
            column_y.input.connect (on_input);

            load_item_settings (item_settings);

            single_column.notify["active"].connect (on_settings_changed);
            column_x.notify["value"].connect (on_settings_changed);
            column_y.notify["value"].connect (on_settings_changed);
            equation.notify["text"].connect (on_settings_changed);
        }

        private void load_item_settings (ColumnsItemSettings item_settings) {
            column_x.set_value (item_settings.column_x);
            column_y.set_value (item_settings.column_y);
            single_column.set_active (item_settings.single_column);
            equation.set_text (item_settings.equation);
        }

        private ColumnsItemSettings get_item_settings () {
            var item_settings = ColumnsItemSettings ();
            item_settings.column_x = (int) column_x.get_value ();
            item_settings.column_y = (int) column_y.get_value ();
            item_settings.single_column = single_column.get_active ();
            item_settings.equation = equation.get_text ().replace (";", "");
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
            spin_button.set_text (Spreadsheet.index_to_label ((int) spin_button.get_value ()));
            return true;
        }

        private int on_input (Adw.SpinRow spin_button, out double new_value) {
            new_value = Spreadsheet.label_to_index (spin_button.get_text ().strip ().up ());
            return 1;
        }
    }

[GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/spreadsheet/box.ui")]
public class SpreadsheetBox : Box {
    [GtkChild]
    public unowned Box items_box { get; }

    private ImportSettings settings;
    private Gee.List<string> item_strings;

    public SpreadsheetBox (ImportSettings settings) {
        this.settings = settings;

        string[] item_string_array = settings.get_string ("items").split (";;");
        item_strings = new Gee.ArrayList<string>.wrap (item_string_array);

        reload_item_groups ();
    }

    private void reload_item_groups () {
        Widget widget;
        while ((widget = items_box.get_last_child ()) != null) {
            items_box.remove (widget);
        }

        for (int i = 0; i < item_strings.size; i++) {
            int index = i;
            var item_settings = ColumnsItemSettings ();
            item_settings.load_from_item_string (item_strings[i]);

            var item_group = new SpreadsheetItemGroup (item_settings, i > 0);
            item_group.set_title (_("Item %d").printf (i + 1));

            item_group.settings_changed.connect ((new_settings) => {
                item_strings[index] = new_settings.to_item_string ();
                update_settings ();
            });

            item_group.remove_request.connect (() => {
                item_strings.remove_at (index);
                update_settings ();
                reload_item_groups ();
            });

            items_box.append (item_group);
        }
    }

    [GtkCallback]
    private void add () {
        item_strings.add (item_strings[0]);
        update_settings ();
        reload_item_groups ();
    }

    private void update_settings () {
        settings.set_string ("items", string.joinv (";;", item_strings.to_array ()));
    }
}
}
