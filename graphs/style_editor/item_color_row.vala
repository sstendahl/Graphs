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
        private unowned Gtk.Button color_button { get; }

        private CssProvider provider = new CssProvider ();
        private string color;
        public StyleColorManager color_manager;

        public signal void color_changed (string color);
        public signal void color_removed ();

        construct {
            this.color_button.get_style_context ().add_provider (
                this.provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );
        }

        public StyleItemColorRow (StyleColorManager color_manager, int index, string color) {
            Object (index: index);
            this.set_title (_("Color %d").printf (index + 1));
            this.color_manager = color_manager;
            this.color = color;
            load_color ();
        }

        private void load_color () {
            this.provider.load_from_string (@"button { color: $color; }");
        }

        [GtkCallback]
        private async void on_color_choose () {
            var dialog = new ColorDialog () { with_alpha = false };
            try {
                RGBA rgba = yield dialog.choose_rgba (
                    (Gtk.Window) this.get_root (),
                    Tools.hex_to_rgba (color),
                    null
                );
                color = Tools.rgba_to_hex (rgba);
                load_color ();
                color_changed.emit (color);
            } catch {}
        }

        [GtkCallback]
        private void on_delete () {
            color_removed.emit ();
        }
    }
}
