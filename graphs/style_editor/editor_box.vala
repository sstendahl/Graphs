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
        private unowned Adw.EntryRow style_name { get; }

        [GtkChild]
        private unowned Gtk.FontDialogButton font_chooser { get; }

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
        private unowned Gtk.ListBox line_colors_box { get; }

        [GtkChild]
        private unowned Gtk.ListBox errbar_line_colors_box { get; }

        [GtkChild]
        private unowned Gtk.Box poor_contrast_warning { get; }

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
            this.parameters = null;
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
            this.markerstyle.set_selected (Markerstyle.from_style (markerstyle));
            linewidth.set_value ((double) parameters.get_param ("lines.linewidth"));
            markersize.set_value ((double) parameters.get_param ("lines.markersize"));

            // Error Bars
            errorbar_capsize.set_value ((double) parameters.get_param ("errorbar.capsize"));
            errorbar_capthick.set_value ((double) parameters.get_param ("errorbar.capthick"));
            errorbar_linewidth.set_value ((double) parameters.get_param ("errorbar.linewidth"));
            errorbar_barsabove.set_active ((bool) parameters.get_param ("errorbar.barsabove"));

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
            tick_labels.set_active ((bool) parameters.get_param ("ticklabels"));
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

        private void update_params () {
            PythonHelper.run_method (parameters, "update");
            notify_property ("parameters");
        }

        [GtkCallback]
        private void on_name() {
            if (parameters == null) return;
            parameters.set_param ("name", style_name.get_text ());
            update_params ();
        }

        [GtkCallback]
        private void on_font () {
            var parameters = this.parameters;
            if (parameters == null) return;

            var font_desc = font_chooser.get_font_desc ();

            parameters.set_param ("font.sans-serif", font_desc.get_family ());

            font_size = font_desc.get_size () / Pango.SCALE;
            parameters.set_param ("font.size", font_size);
            parameters.set_param ("xtick.labelsize", font_size);
            parameters.set_param ("ytick.labelsize", font_size);
            parameters.set_param ("legend.fontsize", font_size);
            parameters.set_param ("figure.labelsize", font_size);

            int font_weight = font_desc.get_weight ();
            parameters.set_param ("font.weight", font_weight);
            parameters.set_param ("axes.titleweight", font_weight);
            parameters.set_param ("axes.labelweight", font_weight);
            parameters.set_param ("figure.titleweight", font_weight);
            parameters.set_param ("figure.labelweight", font_weight);

            EnumClass stylec = (EnumClass) typeof (Pango.Style).class_ref ();
            unowned EnumValue? font_style = stylec.get_value (font_desc.get_style ());
            parameters.set_param ("font.style", font_style.value_nick);

            EnumClass variantc = (EnumClass) typeof (Pango.Variant).class_ref ();
            unowned EnumValue? font_variant = variantc.get_value (font_desc.get_style ());
            parameters.set_param ("font.style", font_variant.value_nick);

            update_params ();
        }

        [GtkCallback]
        private void on_titlesize () {
            var parameters = this.parameters;
            if (parameters == null) return;

            double titlesize = Math.round (titlesize.get_value () / 2 * font_size);
            parameters.set_param ("figure.titlesize", titlesize);
            parameters.set_param ("axes.titlesize", titlesize);

            update_params ();
        }

        [GtkCallback]
        private void on_labelsize () {
            var parameters = this.parameters;
            if (parameters == null) return;

            double labelsize = Math.round (labelsize.get_value () / 2 * font_size);
            parameters.set_param ("axes.labelsize", labelsize);

            update_params ();
        }

        [GtkCallback]
        private void on_linestyle () {
            Linestyle linestyle = (Linestyle) linestyle.get_selected ();
            linewidth.set_sensitive (linestyle != Linestyle.NONE);

            if (parameters == null) return;
            parameters.set_param ("lines.linestyle", linestyle.friendly_string ());
            update_params ();
        }

        [GtkCallback]
        private void on_linewidth () {
            if (parameters == null) return;
            parameters.set_param ("lines.linewidth", linewidth.get_value ());
            update_params ();
        }

        [GtkCallback]
        private void on_markerstyle () {
            Markerstyle markerstyle = (Markerstyle) markerstyle.get_selected ();
            markersize.set_sensitive (markerstyle != Markerstyle.NONE);

            if (parameters == null) return;
            parameters.set_param ("lines.marker", markerstyle.to_style ());
            update_params ();
        }

        [GtkCallback]
        private void on_markersize () {
            if (parameters == null) return;
            parameters.set_param ("lines.markersize", markersize.get_value ());
            update_params ();
        }

        [GtkCallback]
        private void on_errorbar_capsize () {
            if (parameters == null) return;
            parameters.set_param ("errorbar.capsize", errorbar_capsize.get_value ());
            update_params ();
        }

        [GtkCallback]
        private void on_errorbar_capthick () {
            if (parameters == null) return;
            parameters.set_param ("errorbar.capthick", errorbar_capthick.get_value ());
            update_params ();
        }

        [GtkCallback]
        private void on_errorbar_linewidth () {
            if (parameters == null) return;
            parameters.set_param ("errorbar.linewidth", errorbar_linewidth.get_value ());
            update_params ();
        }

        [GtkCallback]
        private void on_errorbar_barsabove () {
            if (parameters == null) return;
            parameters.set_param ("errorbar.barsabove", errorbar_barsabove.get_active ());
            update_params ();
        }

        [GtkCallback]
        private void on_axis_width () {
            if (parameters == null) return;
            parameters.set_param ("axes.linewidth", axis_width.get_value ());
            update_params ();
        }

        [GtkCallback]
        private void on_draw_frame () {
            if (parameters == null) return;
            bool draw_frame = draw_frame.get_active ();
            parameters.set_param ("axes.spines.bottom", draw_frame);
            parameters.set_param ("axes.spines.left", draw_frame);
            parameters.set_param ("axes.spines.top", draw_frame);
            parameters.set_param ("axes.spines.right", draw_frame);
            update_params ();
        }

        [GtkCallback]
        private void on_tick_direction () {
            if (parameters == null) return;
            TickDirection direction = (TickDirection) tick_direction.get_selected ();
            string tick_direction = direction.friendly_string ();
            parameters.set_param ("xtick.direction", tick_direction);
            parameters.set_param ("ytick.direction", tick_direction);
            update_params ();
        }

        [GtkCallback]
        private void on_minor_ticks () {
            if (parameters == null) return;
            bool minor_ticks = minor_ticks.get_active ();
            parameters.set_param ("xtick.minor.visible", minor_ticks);
            parameters.set_param ("ytick.minor.visible", minor_ticks);
            update_params ();
        }

        [GtkCallback]
        private void on_major_tick_width () {
            if (parameters == null) return;
            double major_tick_width = major_tick_width.get_value ();
            parameters.set_param ("xtick.major.width", major_tick_width);
            parameters.set_param ("ytick.major.width", major_tick_width);
            update_params ();
        }

        [GtkCallback]
        private void on_minor_tick_width () {
            if (parameters == null) return;
            double minor_tick_width = minor_tick_width.get_value ();
            parameters.set_param ("xtick.minor.width", minor_tick_width);
            parameters.set_param ("ytick.minor.width", minor_tick_width);
            update_params ();
        }

        [GtkCallback]
        private void on_major_tick_length () {
            if (parameters == null) return;
            double major_tick_length = major_tick_length.get_value ();
            parameters.set_param ("xtick.major.size", major_tick_length);
            parameters.set_param ("ytick.major.size", major_tick_length);
            update_params ();
        }

        [GtkCallback]
        private void on_minor_tick_length () {
            if (parameters == null) return;
            double minor_tick_length = minor_tick_length.get_value ();
            parameters.set_param ("xtick.minor.size", minor_tick_length);
            parameters.set_param ("ytick.minor.size", minor_tick_length);
            update_params ();
        }

        [GtkCallback]
        private void on_tick_labels () {
            if (parameters == null) return;
            parameters.set_param ("ticklabels", tick_labels.get_active ());
            update_params ();
        }

        [GtkCallback]
        private void on_tick_bottom () {
            if (parameters == null) return;
            parameters.set_param ("xtick.bottom", tick_bottom.get_active ());
            update_params ();
        }

        [GtkCallback]
        private void on_tick_left () {
            if (parameters == null) return;
            parameters.set_param ("ytick.left", tick_left.get_active ());
            update_params ();
        }

        [GtkCallback]
        private void on_tick_top () {
            if (parameters == null) return;
            parameters.set_param ("xtick.top", tick_top.get_active ());
            update_params ();
        }

        [GtkCallback]
        private void on_tick_right () {
            if (parameters == null) return;
            parameters.set_param ("ytick.right", tick_right.get_active ());
            update_params ();
        }

        [GtkCallback]
        private async void add_color () {
            var dialog = new Gtk.ColorDialog () { with_alpha = false };
            try {
                Gdk.RGBA color = yield dialog.choose_rgba (window, null, null);
                string hex = Tools.rgba_to_hex (color);
                color_manager.add_color (hex);
            } catch {}
        }

        [GtkCallback]
        private async void add_errbar_color () {
            var dialog = new Gtk.ColorDialog () { with_alpha = false };
            try {
                Gdk.RGBA color = yield dialog.choose_rgba (window, null, null);
                string hex = Tools.rgba_to_hex (color);
                errbar_color_manager.add_color (hex);
            } catch {}
        }
    }
}
