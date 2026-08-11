// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/color-button.ui")]
    public class ColorButton : Gtk.Button {
        [GtkChild]
        private unowned ColorSwatch color_swatch { get; }

        public Gdk.RGBA color {
            get { return color_swatch.color; }
            set { color_swatch.color = value; }
        }

        public signal void color_chosen ();

        [GtkCallback]
        private async void choose_color () {
            var dialog = new Gtk.ColorDialog ();
            try {
                color = yield dialog.choose_rgba (
                    get_root () as Gtk.Window,
                    color,
                    null
                );
                color_chosen.emit ();
            } catch {}
        }
    }
}
