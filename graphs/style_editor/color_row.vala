// SPDX-License-Identifier: GPL-3.0-or-later
using Gdk;
using Gtk;

namespace Graphs {
    /**
     * Style Color Box
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/color-row.ui")]
    public class StyleColorRow : Adw.ActionRow {
        [GtkChild]
        private unowned Image image { get; }

        public RGBA color { get; set; }

        private CssProvider provider = new CssProvider ();

        construct {
            this.image.get_style_context ().add_provider (
                this.provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );
            this.notify["color"].connect (on_color);
        }

        private void on_color () {
            string hex = Tools.rgba_to_hex (color);
            this.provider.load_from_string (@"image { color: $hex; }");
        }

        [GtkCallback]
        private async void on_color_choose () {
            var dialog = new ColorDialog () { with_alpha = false };
            try {
                this.color = yield dialog.choose_rgba (
                    (Gtk.Window) this.get_root (), color, null
                );
            } catch {}
        }
    }
}
