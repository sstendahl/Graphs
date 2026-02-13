// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gdk;
using Gtk;

namespace Graphs {
    private string title_format_function (Scale scale, double value) {
        // Format a float value as a percentage string (integer part only)
        double percentage = (value / 2.0) * 100.0;
        return "%d%%".printf ((int) percentage);
    }

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
        protected unowned StyleColorRow text_color { get; }

        [GtkChild]
        protected unowned StyleColorRow tick_color { get; }

        [GtkChild]
        protected unowned StyleColorRow axis_color { get; }

        [GtkChild]
        protected unowned StyleColorRow grid_color { get; }

        [GtkChild]
        protected unowned StyleColorRow background_color { get; }

        [GtkChild]
        protected unowned StyleColorRow outline_color { get; }

        [GtkChild]
        private unowned ListBox line_colors_box { get; }

        [GtkChild]
        private unowned Box poor_contrast_warning { get; }

        [GtkChild]
        protected unowned Scale errorbar_capsize { get; }

        [GtkChild]
        protected unowned Scale errorbar_capthick { get; }

        [GtkChild]
        protected unowned Scale errorbar_linewidth { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow errorbar_barsabove { get; }

        [GtkChild]
        protected unowned StyleColorRow errorbar_ecolor { get; }

        public signal void params_changed ();

        protected StyleColorManager color_manager { get; set; }
        protected Gtk.Window window { get; set; }

        construct {
            this.color_manager = new StyleColorManager (line_colors_box);

            titlesize.set_format_value_func (title_format_function);
            labelsize.set_format_value_func (title_format_function);
        }

        protected void check_contrast () {
            double contrast = Tools.get_contrast (outline_color.color, text_color.color);
            poor_contrast_warning.set_visible (contrast < 4.5);
        }

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
            var dialog = new ColorDialog () { with_alpha = false };
            try {
                RGBA color = yield dialog.choose_rgba (window, null, null);
                string hex = Tools.rgba_to_hex (color);
                color_manager.add_color (hex);
            } catch {}
        }
    }
}
