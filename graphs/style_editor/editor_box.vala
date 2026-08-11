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

        protected signal void load_request (File file);
        protected signal void save_request (File file);

        construct {
            titlesize.set_format_value_func (title_format_function);
            labelsize.set_format_value_func (title_format_function);
        }

        public void load (File file) {
            load_request.emit (file);
        }

        public void save (File file) {
            save_request.emit (file);
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
