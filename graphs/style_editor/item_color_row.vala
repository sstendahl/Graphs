// SPDX-License-Identifier: GPL-3.0-or-later
using Gdk;
using Gtk;

namespace Graphs {
    /**
     * Style Color Box
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/item-color-row.ui")]
    public class StyleItemColorRow : Adw.ActionRow {
        public int index { get; construct set; }

        [GtkChild]
        private unowned ColorButton color_button { get; }

        public StyleColorManager color_manager;

        public signal void color_changed (string color);
        public signal void color_removed ();

        public StyleItemColorRow (StyleColorManager color_manager, int index, string color) {
            Object (index: index);
            set_title (_("Color %d").printf (index + 1));
            this.color_manager = color_manager;
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
