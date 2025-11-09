// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gdk;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/editor-box.ui")]
    public class StyleEditorBox : Box {
        [GtkChild]
        protected unowned Adw.EntryRow style_name { get; }

        [GtkChild]
        protected unowned FontDialogButton font_chooser { get; }

        [GtkChild]
        protected unowned Scale titlesize { get; }

        [GtkChild]
        protected unowned Scale labelsize { get; }

        [GtkChild]
        protected unowned Adw.ComboRow linestyle { get; }

        [GtkChild]
        protected unowned Scale linewidth { get; }

        [GtkChild]
        protected unowned Adw.ComboRow markers { get; }

        [GtkChild]
        protected unowned Scale markersize { get; }

        [GtkChild]
        protected unowned Scale axis_width { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow draw_frame { get; }

        [GtkChild]
        protected unowned Adw.ComboRow tick_direction { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow minor_ticks { get; }

        [GtkChild]
        protected unowned Scale major_tick_width { get; }

        [GtkChild]
        protected unowned Scale minor_tick_width { get; }

        [GtkChild]
        protected unowned Scale major_tick_length { get; }

        [GtkChild]
        protected unowned Scale minor_tick_length { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow tick_labels { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow tick_bottom { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow tick_left { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow tick_right { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow tick_top { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow show_grid { get; }

        [GtkChild]
        protected unowned Scale grid_linewidth { get; }

        [GtkChild]
        protected unowned Scale grid_opacity { get; }

        [GtkChild]
        protected unowned Scale value_padding { get; }

        [GtkChild]
        protected unowned Scale label_padding { get; }

        [GtkChild]
        protected unowned Scale title_padding { get; }

        [GtkChild]
        protected unowned Button text_color { get; }

        [GtkChild]
        protected unowned Button tick_color { get; }

        [GtkChild]
        protected unowned Button axis_color { get; }

        [GtkChild]
        protected unowned Button grid_color { get; }

        [GtkChild]
        protected unowned Button background_color { get; }

        [GtkChild]
        protected unowned Button outline_color { get; }

        [GtkChild]
        protected unowned ListBox line_colors_box { get; }

        [GtkChild]
        protected unowned Box poor_contrast_warning { get; }

        public signal void params_changed ();

        protected StyleColorManager color_manager { get; set; }
        protected Gtk.Window window { get; set; }

        [GtkCallback]
        private void on_linestyle () {
            linewidth.set_sensitive (linestyle.get_selected () != 0);
        }

        [GtkCallback]
        private void on_markers () {
            markersize.set_sensitive (markers.get_selected () != 0);
        }

        [GtkCallback]
        private async void add_color () {
            var dialog = new ColorDialog ();
            dialog.set_with_alpha (false);
            try {
                RGBA color = yield dialog.choose_rgba (window, null, null);
                string hex = Tools.rgba_to_hex (color);
                color_manager.add_color (hex);
            } catch {}
        }
    }
}
