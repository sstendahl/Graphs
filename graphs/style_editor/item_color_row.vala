// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * Style Color Box
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/item-color-row.ui")]
    public class StyleItemColorRow : Adw.ActionRow {
        public int index { get; construct set; }

        [GtkChild]
        private unowned ColorButton color_button { get; }

        public StyleColorGroup color_group;

        public signal void color_changed (string color);
        public signal void color_removed ();

        public StyleItemColorRow (StyleColorGroup color_group, int index, string color) {
            Object (index: index);
            set_title (_("Color %d").printf (index + 1));
            this.color_group = color_group;
            color_button.color = Tools.hex_to_rgba (color);
        }

        [GtkCallback]
        private async void on_color_chosen () {
            color_changed.emit (Tools.rgba_to_hex (color_button.color));
        }

        [GtkCallback]
        private void on_delete () {
            color_removed.emit ();
        }
    }
}
