// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    private const BindingFlags SYNC = BindingFlags.BIDIRECTIONAL | BindingFlags.SYNC_CREATE;

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/figure-settings/settings-page.ui")]
    public class FigureSettingsPage : Adw.NavigationPage {

        [GtkChild]
        private unowned Adw.EntryRow title_entry { get; }

        [GtkChild]
        public unowned AxisGroup bottom_axis { get; }

        [GtkChild]
        public unowned AxisGroup top_axis { get; }

        [GtkChild]
        public unowned AxisGroup left_axis { get; }

        [GtkChild]
        public unowned AxisGroup right_axis { get; }

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
            AxisGroup axis;
            this.get (direction + "-axis", out axis);

            figure_settings.bind_property (direction + "-label", axis.label_row, "text", SYNC);
            figure_settings.bind_property (direction + "-scale", axis.scale_row, "selected", SYNC);
            figure_settings.bind_property ("min-" + direction, axis, "min", SYNC);
            figure_settings.bind_property ("max-" + direction, axis, "max", SYNC);
            figure_settings.bind_property ("lock-min-" + direction, axis, "min-locked", SYNC);
            figure_settings.bind_property ("lock-max-" + direction, axis, "max-locked", SYNC);
            axis.applied.connect (() => {
                window.data.add_view_history_state ();
                window.canvas.view_changed ();
            });

            axis.set_visible (true);

            // Remove direction prefix if only one is present
            if (x && !both_x) axis.set_title (_("X Axis"));
            else if (!x && !both_y) axis.set_title (_("Y Axis"));
        }

        public void focus_widget (string name) {
            if (name == "title") {
                title_entry.grab_focus ();
                return;
            }

            // Either "<direction>_label" or "<min|max>_<direction>"
            string[] parts = name.split ("_");
            AxisGroup axis;
            if (parts[1] == "label") {
                this.get (parts[0] + "_axis", out axis);
                axis.label_row.grab_focus ();
            } else {
                this.get (parts[1] + "_axis", out axis);
                (parts[0] == "max" ? axis.max_row : axis.min_row).grab_focus ();
            }
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
