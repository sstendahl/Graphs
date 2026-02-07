// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

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
        public unowned Box bottom_limits { get; }

        [GtkChild]
        public unowned Adw.EntryRow min_bottom { get; }

        [GtkChild]
        public unowned Adw.EntryRow max_bottom { get; }

        [GtkChild]
        public unowned Box top_limits { get; }

        [GtkChild]
        public unowned Adw.EntryRow min_top { get; }

        [GtkChild]
        public unowned Adw.EntryRow max_top { get; }

        [GtkChild]
        public unowned Box left_limits { get; }

        [GtkChild]
        public unowned Adw.EntryRow min_left { get; }

        [GtkChild]
        public unowned Adw.EntryRow max_left { get; }

        [GtkChild]
        public unowned Box right_limits { get; }

        [GtkChild]
        public unowned Adw.EntryRow min_right { get; }

        [GtkChild]
        public unowned Adw.EntryRow max_right { get; }

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
        private unowned Label style_name { get; }

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

            bool[] visible_axes = window.data.get_used_positions ();
            bool both_x = visible_axes[0] && visible_axes[1];
            bool both_y = visible_axes[2] && visible_axes[3];
            string[] min_max = {"min", "max"};
            for (int i = 0; i < 4; i++) {
                bool visible = visible_axes[i];
                if (!visible) continue;

                string direction = DIRECTION_NAMES[i];
                bool x = i < 2;

                foreach (string s in min_max) {
                    string key = s + "_" + direction;
                    Adw.EntryRow entry;
                    this.get (key, out entry);
                    figure_settings.bind_property (key, entry, "text", BindingFlags.SYNC_CREATE,
                        (binding, source_value, ref target_value) => {
                            double val = source_value.get_double ();
                            target_value.set_string (Tools.evaluate_double (val));
                            return true;
                        }
                    );

                    entry.apply.connect (() => {
                        double new_val;
                        PythonHelper.evaluate_string (
                            entry.get_text (), out new_val
                        );

                        figure_settings.set (key, new_val);
                        window.data.add_view_history_state ();
                        window.canvas.view_changed ();

                        // workaround button not disappearing when pressed
                        entry.set_show_apply_button (false);
                        entry.set_show_apply_button (true);
                    });

                    // Remove direction prefix if only one is present
                    if (s == "min") {
                        if (x && !both_x) entry.set_title (_("X Axis Minimum"));
                        else if (!x && !both_y) entry.set_title (_("Y Axis Minimum"));
                    } else {
                        if (x && !both_x) entry.set_title (_("X Axis Maximum"));
                        else if (!x && !both_y) entry.set_title (_("Y Axis Maximum"));
                    }
                }

                Adw.ComboRow scale;
                string scale_key = direction + "_scale";
                this.get (scale_key, out scale);
                Adw.EntryRow label;
                this.get (direction + "_label", out label);
                Box limits;
                this.get (direction + "_limits", out limits);

                figure_settings.bind_property (scale_key, scale, "selected", SYNC);

                scale.set_visible (true);
                label.set_visible (true);
                limits.set_visible (true);

                // Remove direction prefix if only one is present
                if (x && !both_x) {
                    scale.set_title (_("X Axis Scale"));
                    label.set_title (_("X Axis Label"));
                }
                else if (!x && !both_y) {
                    scale.set_title (_("Y Axis Scale"));
                    label.set_title (_("Y Axis Label"));
                }
            }
        }

        public void focus_widget (string name) {
            Widget widget;
            this.get (name, out widget);
            widget.grab_focus ();
        }

        [GtkCallback]
        private void on_limit_entry_change (Object object, ParamSpec spec) {
            var entry = object as Adw.EntryRow;
            if (PythonHelper.evaluate_string (entry.get_text ())) {
                entry.remove_css_class ("error");
                entry.set_show_apply_button (true);
            } else {
                entry.add_css_class ("error");
                entry.set_show_apply_button (false);
            }
        }

        [GtkCallback]
        private void open_style_page () {
            var style_page = new StylePage (window);
            window.push_sidebar_page (style_page);
        }

        [GtkCallback]
        private void set_as_default () {
            GLib.Settings settings = Application.get_settings_child ("figure");
            string[] strings = {
                "custom-style", "title",
                "bottom-label", "left-label", "top-label", "right-label"
            };
            string[] bools = {"hide-unselected", "legend", "use-custom-style"};
            string[] enums = {
                "legend-position", "top-scale", "bottom-scale", "left-scale", "right-scale"
            };
            FigureSettings figure_settings = window.data.figure_settings;
            foreach (string key in strings) {
                string val;
                figure_settings.get (key.replace ("-", "_"), out val);
                settings.set_string (key, val);
            }
            foreach (string key in bools) {
                bool val;
                figure_settings.get (key.replace ("-", "_"), out val);
                settings.set_boolean (key, val);
            }
            foreach (string key in enums) {
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
        private unowned GridView style_grid { get; }

        private Window window;

        public StylePage (Window window) {
            this.window = window;

            var factory = new SignalListItemFactory ();
            factory.setup.connect (on_factory_setup);
            factory.bind.connect (on_factory_bind);
            style_grid.set_factory (factory);
            style_grid.set_model (window.data.style_selection_model);
        }

        private void on_factory_setup (Object object) {
            ListItem item = (ListItem) object;
            item.set_child (new StylePreview ());
        }

        private void on_factory_bind (Object object) {
            ListItem item = (ListItem) object;
            StylePreview preview = (StylePreview) item.get_child ();
            preview.style = (Style) item.get_item ();
        }
    }
}
