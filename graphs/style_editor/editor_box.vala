// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    private string title_format_function (Gtk.Scale scale, double value) {
        // Format a float value as a percentage string (integer part only)
        double percentage = (value / 2.0) * 100.0;
        return "%d%%".printf ((int) percentage);
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/editor-box.ui")]
    private class StyleEditorBox : Gtk.Box {
        [GtkChild]
        private unowned Adw.EntryRow style_name { get; }
        [GtkChild]
        private unowned Gtk.FontDialogButton font { get; }
        [GtkChild]
        private unowned Gtk.Scale titlesize { get; }
        [GtkChild]
        private unowned Gtk.Scale labelsize { get; }
        [GtkChild]
        private unowned Adw.ComboRow linestyle { get; }
        [GtkChild]
        private unowned Gtk.Scale linewidth { get; }
        [GtkChild]
        private unowned Adw.ComboRow markerstyle { get; }
        [GtkChild]
        private unowned Gtk.Scale markersize { get; }
        [GtkChild]
        private unowned Gtk.Scale errorbar_capsize { get; }
        [GtkChild]
        private unowned Gtk.Scale errorbar_capthick { get; }
        [GtkChild]
        private unowned Gtk.Scale errorbar_linewidth { get; }
        [GtkChild]
        private unowned Adw.SwitchRow errorbar_barsabove { get; }
        [GtkChild]
        private unowned Gtk.Scale axis_width { get; }
        [GtkChild]
        private unowned Adw.SwitchRow draw_frame { get; }
        [GtkChild]
        private unowned Adw.ComboRow tick_direction { get; }
        [GtkChild]
        private unowned Adw.SwitchRow minor_ticks { get; }
        [GtkChild]
        private unowned Gtk.Scale major_tick_width { get; }
        [GtkChild]
        private unowned Gtk.Scale minor_tick_width { get; }
        [GtkChild]
        private unowned Gtk.Scale major_tick_length { get; }
        [GtkChild]
        private unowned Gtk.Scale minor_tick_length { get; }
        [GtkChild]
        private unowned Adw.SwitchRow tick_labels { get; }
        [GtkChild]
        private unowned Adw.SwitchRow tick_bottom { get; }
        [GtkChild]
        private unowned Adw.SwitchRow tick_left { get; }
        [GtkChild]
        private unowned Adw.SwitchRow tick_right { get; }
        [GtkChild]
        private unowned Adw.SwitchRow tick_top { get; }
        [GtkChild]
        private unowned Adw.SwitchRow show_grid { get; }
        [GtkChild]
        private unowned Gtk.Scale grid_linewidth { get; }
        [GtkChild]
        private unowned Gtk.Scale grid_opacity { get; }
        [GtkChild]
        private unowned Gtk.Scale value_padding { get; }
        [GtkChild]
        private unowned Gtk.Scale label_padding { get; }
        [GtkChild]
        private unowned Gtk.Scale title_padding { get; }
        [GtkChild]
        private unowned ColorRow text_color { get; }
        [GtkChild]
        private unowned ColorRow tick_color { get; }
        [GtkChild]
        private unowned ColorRow axis_color { get; }
        [GtkChild]
        private unowned ColorRow grid_color { get; }
        [GtkChild]
        private unowned ColorRow background_color { get; }
        [GtkChild]
        private unowned ColorRow outline_color { get; }
        [GtkChild]
        private unowned StyleColorGroup line_colors { get; }
        [GtkChild]
        private unowned StyleColorGroup errorbar_colors { get; }

        [GtkChild]
        private unowned Gtk.Box poor_contrast_warning { get; }

        public StyleParameters parameters { get; protected set; }

        construct {
            titlesize.set_format_value_func (title_format_function);
            labelsize.set_format_value_func (title_format_function);
        }

        public void load (StyleParameters style) {
            parameters = null;
            unowned var data = style.data;

            style_name.set_text (style.name);

            font.set_font_desc (data.font);
            titlesize.set_value (data.titlesize);
            labelsize.set_value (data.labelsize);

            linestyle.set_selected (data.linestyle);
            linewidth.set_value (data.linewidth);
            markerstyle.set_selected (data.markerstyle);
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

        private void check_contrast () {
            double contrast = Tools.get_contrast (outline_color.color, text_color.color);
            poor_contrast_warning.set_visible (contrast < 4.5);
        }

        private void update () {
            PythonHelper.run_method (parameters, "update");
        }

        [GtkCallback]
        private void on_font () {
            if (parameters == null) return;
            parameters.data.font = font.get_font_desc ();
            update ();
        }

        [GtkCallback]
        private void on_titlesize () {
            if (parameters == null) return;
            parameters.data.titlesize = titlesize.get_value ();
            update ();
        }

        [GtkCallback]
        private void on_labelsize () {
            if (parameters == null) return;
            parameters.data.labelsize = labelsize.get_value ();
            update ();
        }

        [GtkCallback]
        private void on_linestyle () {
            DataLinestyle val = (DataLinestyle) linestyle.get_selected ();
            linewidth.set_sensitive (val != 0);
            if (parameters == null) return;
            parameters.data.linestyle = val;
            update ();
        }

        [GtkCallback]
        private void on_linewidth () {
            if (parameters == null) return;
            parameters.data.linewidth = linewidth.get_value ();
            update ();
        }

        [GtkCallback]
        private void on_markerstyle () {
            DataMarkerstyle val = (DataMarkerstyle) markerstyle.get_selected ();
            markersize.set_sensitive (val != 0);
            if (parameters == null) return;
            parameters.data.markerstyle = val;
            update ();
        }

        [GtkCallback]
        private void on_markersize () {
            if (parameters == null) return;
            parameters.data.markersize = markersize.get_value ();
            update ();
        }
    }
}
