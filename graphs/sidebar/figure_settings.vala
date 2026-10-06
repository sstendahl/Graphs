// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    private const BindingFlags SYNC = BindingFlags.BIDIRECTIONAL | BindingFlags.SYNC_CREATE;

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/figure-settings/settings-page.ui")]
    public class FigureSettingsPage : Adw.NavigationPage {

        [GtkChild]
        private unowned Adw.EntryRow title_entry { get; }

        [GtkChild]
        public unowned Adw.EntryRow bottom_label { get; }

        [GtkChild]
        public unowned Adw.EntryRow top_label { get; }

        [GtkChild]
        public unowned Adw.EntryRow left_label { get; }

        [GtkChild]
        public unowned Adw.EntryRow right_label { get; }

        [GtkChild]
        public unowned AxisLimitsRow bottom_limits { get; }

        [GtkChild]
        public unowned AxisLimitsRow top_limits { get; }

        [GtkChild]
        public unowned AxisLimitsRow left_limits { get; }

        [GtkChild]
        public unowned AxisLimitsRow right_limits { get; }

        [GtkChild]
        public unowned Adw.ComboRow bottom_scale { get; }

        [GtkChild]
        public unowned Adw.ComboRow top_scale { get; }

        [GtkChild]
        public unowned Adw.ComboRow left_scale { get; }

        [GtkChild]
        public unowned Adw.ComboRow right_scale { get; }

        [GtkChild]
        private unowned Adw.SwitchRow legend { get; }

        [GtkChild]
        private unowned Adw.ComboRow legend_position { get; }

        [GtkChild]
        private unowned Adw.SwitchRow hide_unselected { get; }

        [GtkChild]
        private unowned Gtk.Label style_name { get; }

        private Window window;

        public FigureSettingsPage (Window window) {
            this.window = window;

            FigureSettings figure_settings = window.data.figure_settings;

            figure_settings.bind_property ("title", title_entry, "text", SYNC);
            figure_settings.bind_property ("bottom_label", bottom_label, "text", SYNC);
            figure_settings.bind_property ("top_label", top_label, "text", SYNC);
            figure_settings.bind_property ("left_label", left_label, "text", SYNC);
            figure_settings.bind_property ("right_label", right_label, "text", SYNC);

            figure_settings.bind_property ("legend", legend, "active", SYNC);
            figure_settings.bind_property ("legend_position", legend_position, "selected", SYNC);
            figure_settings.bind_property ("hide_unselected", hide_unselected, "active", SYNC);

            window.data.bind_property ("selected_stylename", style_name, "label", BindingFlags.SYNC_CREATE);

            unowned bool[] visible_axes = window.data.get_used_positions ();
            bool both_x = visible_axes[0] && visible_axes[1];
            bool both_y = visible_axes[2] && visible_axes[3];

            unowned string direction;

            if (visible_axes[0]) {
                direction = XPosition.BOTTOM.friendly_string ();
                handle_widgets (figure_settings, direction, true, both_x, both_y);
            }
            if (visible_axes[1]) {
                direction = XPosition.TOP.friendly_string ();
                handle_widgets (figure_settings, direction, true, both_x, both_y);
            }
            if (visible_axes[2]) {
                direction = YPosition.LEFT.friendly_string ();
                handle_widgets (figure_settings, direction, false, both_x, both_y);
            }
            if (visible_axes[3]) {
                direction = YPosition.RIGHT.friendly_string ();
                handle_widgets (figure_settings, direction, false, both_x, both_y);
            }
        }

        private void handle_widgets (FigureSettings figure_settings, string direction, bool x, bool both_x, bool both_y) {
            Adw.ComboRow scale;
            this.get (direction + "-scale", out scale);
            Adw.EntryRow label;
            this.get (direction + "-label", out label);
            AxisLimitsRow limits;
            this.get (direction + "-limits", out limits);

            figure_settings.bind_property (direction + "-scale", scale, "selected", SYNC);
            figure_settings.bind_property ("min-" + direction, limits, "min", SYNC);
            figure_settings.bind_property ("max-" + direction, limits, "max", SYNC);
            figure_settings.bind_property ("lock-" + direction, limits, "locked", SYNC);
            limits.applied.connect (() => {
                window.data.add_view_history_state ();
                window.canvas.view_changed ();
            });

            scale.set_visible (true);
            label.set_visible (true);
            limits.set_visible (true);

            // Remove direction prefix if only one is present
            if (x && !both_x) {
                scale.set_title (_("X Axis Scale"));
                label.set_title (_("X Axis Label"));
                limits.set_title (_("X Axis"));
            }
            else if (!x && !both_y) {
                scale.set_title (_("Y Axis Scale"));
                label.set_title (_("Y Axis Label"));
                limits.set_title (_("Y Axis"));
            }
        }

        public void focus_widget (string name) {
            if (name.has_prefix ("min_") || name.has_prefix ("max_")) {
                AxisLimitsRow limits;
                this.get (name.substring (4) + "_limits", out limits);
                limits.focus_limit (name.has_prefix ("max_"));
                return;
            }

            Gtk.Widget widget;
            this.get (name, out widget);
            widget.grab_focus ();
        }

        [GtkCallback]
        private void open_style_page () {
            var style_page = new StylePage (window);
            window.push_sidebar_page (style_page);
        }

        private const string[] STRINGS = {
            "custom-style", "title",
            "bottom-label", "left-label", "top-label", "right-label"
        };
        private const string[] BOOLS = {"hide-unselected", "legend", "use-custom-style"};
        private const string[] ENUMS = {
            "legend-position", "top-scale", "bottom-scale", "left-scale", "right-scale"
        };

        [GtkCallback]
        private void set_as_default () {
            Settings settings = Application.get_settings_child ("figure");
            FigureSettings figure_settings = window.data.figure_settings;
            foreach (unowned string key in STRINGS) {
                string val;
                figure_settings.get (key.replace ("-", "_"), out val);
                settings.set_string (key, val);
            }
            foreach (unowned string key in BOOLS) {
                bool val;
                figure_settings.get (key.replace ("-", "_"), out val);
                settings.set_boolean (key, val);
            }
            foreach (unowned string key in ENUMS) {
                int val;
                figure_settings.get (key.replace ("-", "_"), out val);
                settings.set_enum (key, val);
            }
            window.add_toast_string (_("Defaults Updated"));
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/figure-settings/style-page.ui")]
    public class StylePage : Adw.NavigationPage {

        [GtkChild]
        private unowned Gtk.GridView style_grid { get; }

        private Window window;

        public StylePage (Window window) {
            this.window = window;

            var factory = new Gtk.SignalListItemFactory ();
            factory.setup.connect (on_factory_setup);
            factory.bind.connect (on_factory_bind);
            style_grid.set_factory (factory);
            style_grid.set_model (window.data.style_selection_model);
        }

        private void on_factory_setup (Object object) {
            var item = (Gtk.ListItem) object;
            item.set_child (new StylePreview ());
        }

        private void on_factory_bind (Object object) {
            var item = (Gtk.ListItem) object;
            StylePreview preview = (StylePreview) item.get_child ();
            preview.style = (Style) item.get_item ();
        }
    }
}
