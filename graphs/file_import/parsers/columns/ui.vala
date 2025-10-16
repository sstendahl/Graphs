// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/columns/main-group.ui")]
    public class ColumnsGroup : Adw.PreferencesGroup {
        [GtkChild]
        public unowned Adw.ComboRow delimiter { get; }
        [GtkChild]
        public unowned Adw.EntryRow custom_delimiter { get; }
        [GtkChild]
        public unowned Adw.ComboRow separator { get; }
        [GtkChild]
        public unowned Adw.SwitchRow single_column { get; }
        [GtkChild]
        public unowned Adw.SpinRow column_x { get; }
        [GtkChild]
        public unowned Adw.SpinRow column_y { get; }
        [GtkChild]
        public unowned Adw.SpinRow skip_rows { get; }
        [GtkChild]
        public unowned Adw.EntryRow single_equation { get; }

        private ImportSettings settings;

        public ColumnsGroup (ImportSettings settings) {
            this.settings = settings;
            setup_ui ();
        }

        private void load_item_settings (ColumnsItemSettings item_settings) {
            column_x.set_value (item_settings.column_x);
            column_y.set_value (item_settings.column_y);
            single_column.set_active (item_settings.single_column);
            single_equation.set_text (item_settings.equation);
        }

        private ColumnsItemSettings get_item_settings () {
            ColumnsItemSettings item_settings = ColumnsItemSettings ();

            item_settings.column_x = (int) column_x.get_value ();
            item_settings.column_y = (int) column_y.get_value ();
            item_settings.single_column = single_column.get_active ();
            item_settings.equation = single_equation.get_text ().replace (";", "");

            return item_settings;
        }

        private void update_items () {
            settings.set_string ("items", get_item_settings ().to_item_string ());
        }

        private void setup_ui () {
            delimiter.set_selected (ColumnsDelimiter.parse (settings.get_string ("delimiter")));
            delimiter.notify["selected"].connect (() => {
                ColumnsDelimiter selected = (ColumnsDelimiter) delimiter.get_selected ();
                settings.set_string ("delimiter", selected.friendly_string ());
                custom_delimiter.set_sensitive (selected == ColumnsDelimiter.CUSTOM);
            });

            custom_delimiter.set_sensitive (delimiter.get_selected () == ColumnsDelimiter.CUSTOM);
            custom_delimiter.set_text (settings.get_string ("custom-delimiter"));
            custom_delimiter.notify["text"].connect (() => {
                settings.set_string ("custom-delimiter", custom_delimiter.get_text ());
            });

            separator.set_selected (ColumnsSeparator.parse (settings.get_string ("separator")));
            separator.notify["selected"].connect (() => {
                settings.set_string ("separator", ((ColumnsSeparator) separator.get_selected ()).friendly_string ());
            });

            skip_rows.set_value (settings.get_int ("skip-rows"));
            skip_rows.notify["value"].connect (() => {
                settings.set_int ("skip-rows", (int) skip_rows.get_value ());
            });

            string item_string = settings.get_string ("items");
            ColumnsItemSettings item_settings = ColumnsItemSettings ();
            item_settings.load_from_item_string (item_string);
            load_item_settings (item_settings);

            single_column.notify["active"].connect (update_items);
            column_x.notify["value"].connect (update_items);
            column_y.notify["value"].connect (update_items);
            single_equation.notify["text"].connect (update_items);
        }
    }
}
