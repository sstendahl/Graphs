// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/columns/box.ui")]
    public class ColumnsBox : Box {
        [GtkChild]
        public unowned Box items_box { get; }

        private ImportSettings settings;
        private Gee.List<string> item_strings;

        public ColumnsBox (ImportSettings settings) {
            this.settings = settings;

            prepend (new ColumnsGroup (settings));

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

                var item_group = new ColumnsItemGroup (item_settings, i > 0);
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

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/columns/main-group.ui")]
    public class ColumnsGroup : Adw.PreferencesGroup {
        [GtkChild]
        public unowned Adw.ComboRow delimiter { get; }
        [GtkChild]
        public unowned Adw.EntryRow custom_delimiter { get; }
        [GtkChild]
        public unowned Adw.ComboRow separator { get; }
        [GtkChild]
        public unowned Adw.SpinRow skip_rows { get; }

        public ColumnsGroup (ImportSettings settings) {
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
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/columns/item-group.ui")]
    public class ColumnsItemGroup : Adw.PreferencesGroup {
        [GtkChild]
        public unowned Adw.SpinRow column_x { get; }
        [GtkChild]
        public unowned Adw.SpinRow column_y { get; }
        [GtkChild]
        public unowned Adw.SwitchRow single_column { get; }
        [GtkChild]
        public unowned Adw.EntryRow equation { get; }
        [GtkChild]
        public unowned Adw.SwitchRow use_xerr { get; }
        [GtkChild]
        public unowned Adw.SwitchRow use_yerr { get; }
        [GtkChild]
        public unowned Adw.SpinRow column_xerr { get; }
        [GtkChild]
        public unowned Adw.SpinRow column_yerr { get; }
        [GtkChild]
        public unowned Button remove_button { get; }

        public signal void settings_changed (ColumnsItemSettings new_settings);
        public signal void remove_request ();

        public ColumnsItemGroup (ColumnsItemSettings item_settings, bool removable) {
            remove_button.set_visible (removable);

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
            ColumnsItemSettings item_settings = ColumnsItemSettings ();

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
    }
}
