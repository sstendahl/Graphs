// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gdk;
using Gtk;

namespace Graphs {
    private string title_format_function (Gtk.Scale scale, double value) {
        // Format a float value as a percentage string (integer part only)
        double percentage = (value / 2.0) * 100.0;
        return "%d%%".printf ((int) percentage);
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/editor-box.ui")]
    public class StyleEditorBox : Box {
        [GtkChild]
        private unowned Adw.EntryRow style_name { get; }

        [GtkChild]
        private unowned FontDialogButton font_chooser { get; }

        [GtkChild]
        private unowned Gtk.Scale titlesize { get; }

        [GtkChild]
        private unowned Gtk.Scale labelsize { get; }

        [GtkChild]
        private unowned Adw.ComboRow linestyle { get; }

        [GtkChild]
        private unowned Gtk.Scale linewidth { get; }

        [GtkChild]
        private unowned Adw.ComboRow markers { get; }

        [GtkChild]
        private unowned Gtk.Scale markersize { get; }

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
        private unowned StyleColorRow text_color { get; }

        [GtkChild]
        private unowned StyleColorRow tick_color { get; }

        [GtkChild]
        private unowned StyleColorRow axis_color { get; }

        [GtkChild]
        private unowned StyleColorRow grid_color { get; }

        [GtkChild]
        private unowned StyleColorRow background_color { get; }

        [GtkChild]
        private unowned StyleColorRow outline_color { get; }

        [GtkChild]
        private unowned ListBox line_colors_box { get; }

        [GtkChild]
        private unowned ListBox errbar_line_colors_box { get; }

        [GtkChild]
        private unowned Box poor_contrast_warning { get; }

        [GtkChild]
        private unowned Gtk.Scale errorbar_capsize { get; }

        [GtkChild]
        private unowned Gtk.Scale errorbar_capthick { get; }

        [GtkChild]
        private unowned Gtk.Scale errorbar_linewidth { get; }

        [GtkChild]
        private unowned Adw.SwitchRow errorbar_barsabove { get; }

        public StyleParameters parameters { get; private set; }

        private StyleColorManager color_manager;
        private StyleColorManager errbar_color_manager;
        private Gtk.Window window;

        private int font_size;

        construct {
            this.color_manager = new StyleColorManager (line_colors_box);
            this.errbar_color_manager = new StyleColorManager (errbar_line_colors_box);

            titlesize.set_format_value_func (title_format_function);
            labelsize.set_format_value_func (title_format_function);
        }

        public StyleEditorBox (Gtk.Window window) {
            this.window = window;
        }

        public void load (File file) {
            var parameters = StyleManager.get_style_params (file, StyleManager.get_system_style_params ());

            style_name.set_text (parameters.get_name ());

            // Font
            var font_desc = new Pango.FontDescription ();
            font_size = (int) parameters.get_param ("font.size").get_double ();
            var font_family = (string) parameters.get_param ("font.sans-serif");
            int font_weight = (int) parameters.get_param ("font.weight");
            Pango.Style font_style;
            Pango.parse_style ((string) parameters.get_param ("font.style"), out font_style, true);
            Pango.Variant font_variant;
            Pango.parse_variant ((string) parameters.get_param ("font.variant"), out font_variant, true);
            font_desc.set_size (font_size * Pango.SCALE);
            font_desc.set_family (font_family);
            font_desc.set_weight (font_weight);
            font_desc.set_style (font_style);
            font_desc.set_variant (font_variant);
            font_chooser.set_font_desc (font_desc);

            double title_size = (double) parameters.get_param ("figure.titlesize");
            double label_size = (double) parameters.get_param ("axes.labelsize");
            titlesize.set_value (Math.round (title_size * 2 / font_size));
            labelsize.set_value (Math.round (label_size * 2 / font_size));

            // Lines
            string linestyle = (string) parameters.get_param ("lines.linestyle");
            string markerstyle = (string) parameters.get_param ("lines.marker");
            this.linestyle.set_selected (Linestyle.from_string (linestyle));
            this.markers.set_selected (Markerstyle.from_style (markerstyle));
            linewidth.set_value ((double) parameters.get_param ("lines.linewidth"));
            markersize.set_value ((double) parameters.get_param ("lines.markersize"));

            // Error Bars
            errorbar_capsize.set_value ((double) parameters.get_param ("errorbar.capsize", true));
            errorbar_capthick.set_value ((double) parameters.get_param ("errorbar.capthick", true));
            errorbar_linewidth.set_value ((double) parameters.get_param ("errorbar.linewidth", true));
            errorbar_barsabove.set_active ((bool) parameters.get_param ("errorbar.barsabove", true));

            // Axes
            axis_width.set_value ((double) parameters.get_param ("axes.linewidth"));
            draw_frame.set_active ((bool) parameters.get_param ("axes.spines.bottom"));

            // Ticks
            string tick_direction = (string) parameters.get_param ("xtick.direction");
            this.tick_direction.set_selected (TickDirection.from_string (tick_direction));
            minor_ticks.set_active ((bool) parameters.get_param ("xtick.minor.visible"));
            major_tick_width.set_value ((double) parameters.get_param ("xtick.major.width"));
            minor_tick_width.set_value ((double) parameters.get_param ("xtick.minor.width"));
            major_tick_length.set_value ((double) parameters.get_param ("xtick.major.size"));
            minor_tick_length.set_value ((double) parameters.get_param ("xtick.minor.size"));
            tick_labels.set_active ((bool) parameters.get_param ("ticklabels", true));
            tick_bottom.set_active ((bool) parameters.get_param ("xtick.bottom"));
            tick_left.set_active ((bool) parameters.get_param ("ytick.left"));
            tick_top.set_active ((bool) parameters.get_param ("xtick.top"));
            tick_right.set_active ((bool) parameters.get_param ("ytick.right"));

            // Grid
            show_grid.set_active ((bool) parameters.get_param ("axes.grid"));
            grid_linewidth.set_value ((double) parameters.get_param ("grid.linewidth"));
            grid_opacity.set_value ((double) parameters.get_param ("grid.alpha"));

            // Padding
            value_padding.set_value ((double) parameters.get_param ("xtick.major.pad"));
            label_padding.set_value ((double) parameters.get_param ("axes.labelpad"));
            title_padding.set_value ((double) parameters.get_param ("axes.titlepad"));

            // Colors
            text_color.set_color_string ((string) parameters.get_param ("text.color"));
            tick_color.set_color_string ((string) parameters.get_param ("xtick.color"));
            axis_color.set_color_string ((string) parameters.get_param ("axes.edgecolor"));
            grid_color.set_color_string ((string) parameters.get_param ("grid.color"));
            background_color.set_color_string ((string) parameters.get_param ("axes.facecolor"));
            outline_color.set_color_string ((string) parameters.get_param ("figure.facecolor"));

            color_manager.set_colors (parameters.get_color_cycle ());
            errbar_color_manager.set_colors (parameters.get_errorbar_cycle ());

            check_contrast ();

            this.parameters = parameters;
        }

        public void save (File file) {
            StyleManager.save_style_params (parameters, file);
        }

        private void check_contrast () {
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

        [GtkCallback]
        private async void add_errbar_color () {
            var dialog = new ColorDialog () { with_alpha = false };
            try {
                RGBA color = yield dialog.choose_rgba (window, null, null);
                string hex = Tools.rgba_to_hex (color);
                errbar_color_manager.add_color (hex);
            } catch {}
        }
    }
}
