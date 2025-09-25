// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    enum ColumnsDelimiter {
        WHITESPACE,
        TAB,
        COLON,
        SEMICOLON,
        COMMA,
        PERIOD,
        CUSTOM;

        public string friendly_string () {
            return this.to_string ()[25:].down ();
        }

        public static ColumnsDelimiter parse (string delimiter) {
            switch (delimiter) {
                case "whitespace": return ColumnsDelimiter.WHITESPACE;
                case "tab": return ColumnsDelimiter.TAB;
                case "colon": return ColumnsDelimiter.COLON;
                case "semicolon": return ColumnsDelimiter.SEMICOLON;
                case "comma": return ColumnsDelimiter.COMMA;
                case "period": return ColumnsDelimiter.PERIOD;
                case "custom": return ColumnsDelimiter.CUSTOM;
                default: assert_not_reached ();
            }
        }
    }

    enum ColumnsSeparator {
        COMMA,
        PERIOD;

        public string friendly_string () {
            return this.to_string ()[25:].down ();
        }

        public static ColumnsSeparator parse (string separator) {
            switch (separator) {
                case "comma": return ColumnsSeparator.COMMA;
                case "period": return ColumnsSeparator.PERIOD;
                default: assert_not_reached ();
            }
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/import/mode-columns.ui")]
    public class ColumnsGroup : Adw.PreferencesGroup {

        [GtkChild]
        public unowned Adw.ComboRow delimiter { get; }

        [GtkChild]
        public unowned Adw.EntryRow custom_delimiter { get; }

        [GtkChild]
        public unowned Adw.ComboRow separator { get; }

        [GtkChild]
        public unowned Adw.SpinRow column_x { get; }

        [GtkChild]
        public unowned Adw.SpinRow column_y { get; }

        [GtkChild]
        public unowned Adw.SpinRow skip_rows { get; }

        public ColumnsGroup (ImportSettings settings) {
            delimiter.set_selected (ColumnsDelimiter.parse (settings.get_string ("delimiter")));
            delimiter.notify["selected"].connect (() => {
                ColumnsDelimiter selected = (ColumnsDelimiter) delimiter.get_selected ();
                settings.set_string ("delimiter", selected.friendly_string ());
                custom_delimiter.set_sensitive (selected == ColumnsDelimiter.CUSTOM);
            });

            custom_delimiter.set_text (settings.get_string ("custom-delimiter"));
            custom_delimiter.notify["text"].connect (() => {
                settings.set_string ("custom-delimiter", custom_delimiter.get_text ());
            });

            separator.set_selected (ColumnsSeparator.parse (settings.get_string ("separator")));
            separator.notify["selected"].connect (() => {
                settings.set_string ("separator", ((ColumnsSeparator) separator.get_selected ()).friendly_string ());
            });

            column_x.set_value (settings.get_int ("column-x"));
            column_x.notify["value"].connect (() => {
                settings.set_int ("column-x", (int) column_x.get_value ());
            });

            column_y.set_value (settings.get_int ("column-y"));
            column_y.notify["value"].connect (() => {
                settings.set_int ("column-y", (int) column_y.get_value ());
            });

            skip_rows.set_value (settings.get_int ("skip-rows"));
            skip_rows.notify["value"].connect (() => {
                settings.set_int ("skip-rows", (int) skip_rows.get_value ());
            });
        }
    }
}
