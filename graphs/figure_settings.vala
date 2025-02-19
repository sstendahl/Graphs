// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Figure settings
     */
    public class FigureSettings : Object {

        public string title { get; set; default = ""; }
        public string bottom_label { get; set; default = ""; }
        public string left_label { get; set; default = ""; }
        public string top_label { get; set; default = ""; }
        public string right_label { get; set; default = ""; }

        public int bottom_scale { get; set; default = 0; }
        public int left_scale { get; set; default = 0; }
        public int top_scale { get; set; default = 0; }
        public int right_scale { get; set; default = 0; }

        public bool legend { get; set; default = true; }
        public int legend_position { get; set; default = 0; }
        public bool use_custom_style { get; set; default = false; }
        public string custom_style { get; set; default = "Adwaita"; }
        public bool hide_unselected { get; set; default = false; }

        public double min_bottom { get; set; default = 0; }
        public double max_bottom { get; set; default = 1; }
        public double min_left { get; set; default = 0; }
        public double max_left { get; set; default = 10; }
        public double min_top { get; set; default = 0; }
        public double max_top { get; set; default = 1; }
        public double min_right { get; set; default = 0; }
        public double max_right { get; set; default = 10; }

        public double min_selected { get; set; default = 0; }
        public double max_selected { get; set; default = 0; }

        public FigureSettings (GLib.Settings settings) {
            Object (
                bottom_scale: settings.get_enum ("bottom-scale"),
                left_scale: settings.get_enum ("left-scale"),
                right_scale: settings.get_enum ("right-scale"),
                top_scale: settings.get_enum ("top-scale"),
                title: settings.get_string ("title"),
                bottom_label: settings.get_string ("bottom-label"),
                left_label: settings.get_string ("left-label"),
                top_label: settings.get_string ("top-label"),
                right_label: settings.get_string ("right-label"),
                legend: settings.get_boolean ("legend"),
                use_custom_style: settings.get_boolean ("use-custom-style"),
                legend_position: settings.get_enum ("legend-position"),
                custom_style: settings.get_string ("custom-style")
            );
        }

        public double[] get_limits () {
            double[] limits = {};
            foreach (string limit_name in LIMIT_NAMES) {
                double limit;
                get (limit_name, out limit);
                limits += limit;
            }
            return limits;
        }

        public void set_limits (double[] limits)
        requires (limits.length == 8) {
            for (int i = 0; i < LIMIT_NAMES.length; i++) {
                set (LIMIT_NAMES[i], limits[i]);
            }
        }

        public void set_selection_range (double minimum, double maximum)
        requires (0 <= minimum <= 1)
        requires (0 <= maximum <= 1)
        requires (minimum <= maximum) {
            this.min_selected = minimum;
            this.max_selected = maximum;
        }
    }

    private const string PAGE_RESOURCE = "/se/sjoerd/Graphs/ui/figure-settings-page.ui";

    /**
     * Figure settings dialog
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/figure-settings-dialog.ui")]
    public class FigureSettingsDialog : Adw.Dialog {

        [GtkChild]
        public unowned Adw.NavigationView navigation_view { get; }

        [GtkChild]
        private unowned GridView style_grid { get; }

        [GtkChild]
        private unowned Adw.NavigationPage style_overview { get; }

        [GtkChild]
        private unowned Adw.ToastOverlay toast_overlay { get; }

        private Application application;
        private Window window;
        private Adw.NavigationPage settings_page;

        public FigureSettingsDialog (Window window, string? highlighted = null) {
            this.window = window;
            this.application = window.application as Application;
            FigureSettings figure_settings = window.data.figure_settings;
            GLib.Settings settings = application.get_settings_child ("figure");

            var builder = new Builder.from_resource (PAGE_RESOURCE);

            this.settings_page = builder.get_object ("settings_page") as Adw.NavigationPage;
            navigation_view.push (settings_page);
            foreach (string key in settings.settings_schema.list_keys ()) {
                if (key[-5:] == "style") continue;
                key = key.replace ("-", "_");
                Object object = builder.get_object (key);
                if (object is Adw.EntryRow) {
                    figure_settings.bind_property (key, object, "text", 1 | 2);
                }
                else if (object is Adw.ComboRow) {
                    figure_settings.bind_property (key, object, "selected", 1 | 2);
                }
                else if (object is Adw.SwitchRow) {
                    figure_settings.bind_property (key, object, "active", 1 | 2);
                }
                else assert_not_reached ();
            }

            bool[] visible_axes = window.data.get_used_positions ();
            bool both_x = visible_axes[0] && visible_axes[1];
            bool both_y = visible_axes[2] && visible_axes[3];
            string[] min_max = {"min", "max"};
            for (int i = 0; i < 4; i++) {
                string direction = DIRECTION_NAMES[i];
                bool visible = visible_axes[i];
                bool x = i < 2;
                if (visible) {
                    foreach (string s in min_max) {
                        string key = s + "_" + direction;
                        var entry = builder.get_object (key) as Adw.EntryRow;
                        double val;
                        figure_settings.get (key, out val);
                        entry.set_text (val.to_string ());
                        entry.notify["text"].connect (() => {
                            double? new_val = application.python_helper.evaluate_string (
                                entry.get_text ()
                            );
                            if (new_val == null) {
                                entry.add_css_class ("error");
                            } else {
                                entry.remove_css_class ("error");
                                figure_settings.set (key, (double) new_val);
                                window.canvas.view_changed ();
                            }
                        });
                        if (s == "min") {
                            if (x && !both_x) entry.set_title (_("X Axis Minimum"));
                            else if (!x && !both_y) entry.set_title (_("Y Axis Minimum"));
                        } else {
                            if (x && !both_x) entry.set_title (_("X Axis Maximum"));
                            else if (!x && !both_y) entry.set_title (_("Y Axis Maximum"));
                        }
                    }
                    var scale = builder.get_object (direction + "_scale") as Adw.ComboRow;
                    var label = builder.get_object (direction + "_label") as Adw.EntryRow;
                    var limits = builder.get_object (direction + "_limits") as Box;
                    scale.set_visible (true);
                    label.set_visible (true);
                    limits.set_visible (true);
                    if (x && !both_x) {
                        scale.set_title (_("X Axis Scale"));
                        label.set_title (_("X Axis Label"));
                    }
                    else if (!x && !both_y) {
                        scale.set_title (_("Y Axis Scale"));
                        label.set_title (_("X Axis Label"));
                    }
                }
            }
            var style_name = builder.get_object ("style_name") as Label;
            window.data.bind_property (
                "selected_stylename", style_name, "label", 2
            );

            var factory = new SignalListItemFactory ();
            factory.setup.connect (on_factory_setup);
            factory.bind.connect (on_factory_bind);
            style_grid.set_factory (factory);
            style_grid.set_model (window.data.style_selection_model);

            var style_row = builder.get_object ("style_row") as Adw.ActionRow;
            style_row.activated.connect (() => {
                navigation_view.push (style_overview);
            });
            var button = builder.get_object ("set_as_default") as Adw.ButtonRow;
            button.activated.connect (set_as_default);

            var action_group = new SimpleActionGroup ();
            var import_action = new SimpleAction ("import_style", null);
            import_action.activate.connect (() => {
                var dialog = new FileDialog ();
                dialog.set_filters (get_mplstyle_file_filters ());
                dialog.open.begin (window, null, (d, response) => {
                try {
                    var file = dialog.open.end (response);
                    var style_dir = application.figure_style_manager.style_dir;
                    string filename = Tools.get_filename (file);
                    if (!filename.has_suffix (".mplstyle")) return;
                    var destination = style_dir.get_child_for_display_name (filename);
                    uint i = 1;
                    while (destination.query_exists ()) {
                        var new_filename = new StringBuilder ();
                        new_filename
                            .append (filename[:-9])
                            .append ("-")
                            .append (i.to_string ())
                            .append (".mplstyle");
                        destination = style_dir.get_child_for_display_name (new_filename.free_and_steal ());
                        i++;
                    }
                    file.copy_async.begin (destination, FileCopyFlags.NONE);
                } catch {}
            });
            });
            action_group.add_action (import_action);
            var create_action = new SimpleAction ("create_style", null);
            create_action.activate.connect (() => {
                new AddStyleDialog (
                    application.figure_style_manager,
                    this,
                    window.data.figure_settings
                );
            });
            action_group.add_action (create_action);
            insert_action_group ("figure_settings", action_group);

            present (window);
            if (highlighted != null) {
                var widget = builder.get_object (highlighted) as Widget;
                widget.grab_focus ();
            }
        }

        [GtkCallback]
        private void on_closed () {
            window.data.add_history_state ();
            window.data.add_view_history_state ();
        }

        private void set_as_default () {
            GLib.Settings settings = application.get_settings_child ("figure");
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
            toast_overlay.add_toast (new Adw.Toast (_("Defaults Updated")));
        }

        private void on_factory_setup (Object object) {
            ListItem item = object as ListItem;
            item.set_child (new StylePreview ());
        }

        private void on_factory_bind (Object object) {
            ListItem item = object as ListItem;
            StylePreview preview = item.get_child () as StylePreview;
            Style style = item.get_item () as Style;
            preview.style = style;
            if (style.mutable && !preview.menu_button.get_visible ()) {
                preview.menu_button.set_visible (true);

                var action_group = new SimpleActionGroup ();
                var open_action = new SimpleAction ("open", null);
                open_action.activate.connect (() => {
                    var style_editor = application.create_style_editor ();
                    style_editor.load (style.file);
                    style_editor.present ();
                });
                action_group.add_action (open_action);
                var open_with_action = new SimpleAction ("open_with", null);
                open_with_action.activate.connect (() => {
                    var launcher = new FileLauncher (style.file);
                    launcher.set_always_ask (true);
                    launcher.launch.begin (window, null);
                });
                action_group.add_action (open_with_action);
                var delete_action = new SimpleAction ("delete", null);
                delete_action.activate.connect (() => {
                    var dialog = Tools.build_dialog ("delete_style") as Adw.AlertDialog;
                    string msg = _("Are you sure you want to delete %s?");
                    dialog.set_body (msg.printf (style.name));
                    dialog.response.connect ((d, response) => {
                        if (response != "delete") return;
                        try {
                            style.file.trash ();
                        } catch {
                            assert_not_reached ();
                        }
                    });
                    dialog.present (this);
                });
                action_group.add_action (delete_action);
                preview.menu_button.insert_action_group ("style", action_group);
            }
        }
    }
}
