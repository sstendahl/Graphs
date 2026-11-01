// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    private string title_format_function (Gtk.Scale scale, double value) {
        // Format a float value as a percentage string (integer part only)
        double percentage = (value / 2.0) * 100.0;
        return "%d%%".printf ((int) percentage);
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/editor-box.ui")]
    public class StyleEditorBox : Gtk.Box {
        [GtkChild]
        protected unowned Adw.EntryRow style_name { get; }

        [GtkChild]
        protected unowned Gtk.FontDialogButton font_chooser { get; }

        [GtkChild]
        protected unowned Gtk.Scale titlesize { get; }

        [GtkChild]
        protected unowned Gtk.Scale labelsize { get; }

        [GtkChild]
        protected unowned Adw.ComboRow linestyle { get; }

        [GtkChild]
        protected unowned Gtk.Scale linewidth { get; }

        [GtkChild]
        protected unowned Adw.ComboRow markers { get; }

        [GtkChild]
        protected unowned Gtk.Scale markersize { get; }

        [GtkChild]
        protected unowned Gtk.Scale axis_width { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow draw_frame { get; }

        [GtkChild]
        protected unowned Adw.ComboRow tick_direction { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow minor_ticks { get; }

        [GtkChild]
        protected unowned Gtk.Scale major_tick_width { get; }

        [GtkChild]
        protected unowned Gtk.Scale minor_tick_width { get; }

        [GtkChild]
        protected unowned Gtk.Scale major_tick_length { get; }

        [GtkChild]
        protected unowned Gtk.Scale minor_tick_length { get; }

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
        protected unowned Gtk.Scale grid_linewidth { get; }

        [GtkChild]
        protected unowned Gtk.Scale grid_opacity { get; }

        [GtkChild]
        protected unowned Gtk.Scale value_padding { get; }

        [GtkChild]
        protected unowned Gtk.Scale label_padding { get; }

        [GtkChild]
        protected unowned Gtk.Scale title_padding { get; }

        [GtkChild]
        protected unowned ColorRow text_color { get; }

        [GtkChild]
        protected unowned ColorRow tick_color { get; }

        [GtkChild]
        protected unowned ColorRow axis_color { get; }

        [GtkChild]
        protected unowned ColorRow grid_color { get; }

        [GtkChild]
        protected unowned ColorRow background_color { get; }

        [GtkChild]
        protected unowned ColorRow outline_color { get; }

        [GtkChild]
        protected unowned StyleColorGroup line_colors { get; }

        [GtkChild]
        protected unowned StyleColorGroup errorbar_colors { get; }

        [GtkChild]
        private unowned Gtk.Box poor_contrast_warning { get; }

        [GtkChild]
        protected unowned Gtk.Scale errorbar_capsize { get; }

        [GtkChild]
        protected unowned Gtk.Scale errorbar_capthick { get; }

        [GtkChild]
        protected unowned Gtk.Scale errorbar_linewidth { get; }

        [GtkChild]
        protected unowned Adw.SwitchRow errorbar_barsabove { get; }

        public StyleParameters parameters { get; protected set; }

        construct {
            titlesize.set_format_value_func (title_format_function);
            labelsize.set_format_value_func (title_format_function);
        }

        public void load (StyleParameters style) {
            parameters = null;
            unowned var data = style.data;

            style_name.set_text (style.name);

            font_chooser.set_font_desc (data.font);
            titlesize.set_value (data.titlesize);
            labelsize.set_value (data.labelsize);

            linestyle.set_selected (data.linestyle);
            linewidth.set_value (data.linewidth);
            markers.set_selected (data.markerstyle);
            markersize.set_value (data.markersize);

            errorbar_capsize.set_value (data.errorbar_capsize);
            errorbar_capthick.set_value (data.errorbar_capthick);
            errorbar_linewidth.set_value (data.errorbar_linewidth);
            errorbar_barsabove.set_active (data.errorbar_barsabove);

            axis_width.set_value (data.axis_width);
            draw_frame.set_active (data.draw_frame);

            tick_direction.set_selected (data.tick_direction);
            minor_ticks.set_active (data.minor_ticks);
            major_tick_width.set_value (data.major_tick_width);
            minor_tick_width.set_value (data.minor_tick_width);
            major_tick_length.set_value (data.major_tick_width);
            minor_tick_length.set_value (data.minor_tick_length);
            tick_labels.set_active (data.tick_labels);
            tick_bottom.set_active (data.tick_bottom);
            tick_left.set_active (data.tick_left);
            tick_top.set_active (data.tick_top);
            tick_right.set_active (data.tick_right);

            show_grid.set_active (data.show_grid);
            grid_linewidth.set_value (data.grid_linewidth);
            grid_opacity.set_value (data.grid_opacity);

            value_padding.set_value (data.value_padding);
            label_padding.set_value (data.label_padding);
            title_padding.set_value (data.title_padding);

            text_color.color = Tools.hex_to_rgba (data.text_color);
            tick_color.color = Tools.hex_to_rgba (data.tick_color);
            axis_color.color = Tools.hex_to_rgba (data.axis_color);
            grid_color.color = Tools.hex_to_rgba (data.grid_color);
            background_color.color = Tools.hex_to_rgba (data.background_color);
            outline_color.color = Tools.hex_to_rgba (data.outline_color);

            line_colors.set_colors (data.color_cycle);
            errorbar_colors.set_colors (data.errorbar_cycle);

            check_contrast ();

            parameters = style;
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
    }
}
