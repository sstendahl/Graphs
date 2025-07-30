// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    private const string PAGE_RESOURCE = "/se/sjoerd/Graphs/ui/figure-settings-page.ui";

    private const string SETTINGS_RESOURCE = "/se/sjoerd/Graphs/ui/sidebar/figure-settings/settings.ui";

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/figure-settings/page.ui")]
    public class FigureSettingsPage : Adw.NavigationPage {

        [GtkChild]
        public unowned Adw.Bin settings_bin { get; }

        private Application application;
        private Window window;

        public FigureSettingsPage (Window window, string? highlighted = null) {
            this.window = window;
            this.application = window.application as Application;

            FigureSettings figure_settings = window.data.figure_settings;
            GLib.Settings settings = application.get_settings_child ("figure");

            var builder = new Builder.from_resource (SETTINGS_RESOURCE);
            var settings_box = builder.get_object ("settings_box") as Box;
            settings_bin.set_child (settings_box);

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
                        figure_settings.bind_property (key, entry, "text", BindingFlags.SYNC_CREATE);
                        entry.notify["text"].connect (() => {
                            double? new_val = application.python_helper.evaluate_string (
                                entry.get_text ()
                            );
                            if (new_val == null) {
                                entry.add_css_class ("error");
                                entry.set_show_apply_button (false);
                            } else {
                                entry.remove_css_class ("error");
                                entry.set_show_apply_button (true);
                            }
                        });
                        entry.apply.connect (() => {
                            double? new_val = application.python_helper.evaluate_string (
                                entry.get_text ()
                            );
                            assert (new_val != null);

                            figure_settings.set (key, (double) new_val);
                            window.data.add_view_history_state ();
                            window.canvas.view_changed ();

                            // workaround button not disappearing when pressed
                            entry.set_show_apply_button (false);
                            entry.set_show_apply_button (true);
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

            var style_row = builder.get_object ("style_row") as Adw.ActionRow;
            style_row.activated.connect (() => {
                var style_page = new StylePage (window);
                window.push_sidebar_page (style_page);
            });

            var default_button = builder.get_object ("set_as_default") as Adw.ButtonRow;
            default_button.activated.connect (set_as_default);

            if (highlighted != null) {
                var widget = builder.get_object (highlighted) as Widget;
                widget.grab_focus ();
            }
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
            window.add_toast_string (_("Defaults Updated"));
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/figure-settings/style-page.ui")]
    public class StylePage : Adw.NavigationPage {

        [GtkChild]
        private unowned GridView style_grid { get; }

        private Application application;
        private Window window;

        public StylePage (Window window) {
            this.window = window;
            this.application = window.application as Application;

            var factory = new SignalListItemFactory ();
            factory.setup.connect (on_factory_setup);
            factory.bind.connect (on_factory_bind);
            style_grid.set_factory (factory);
            style_grid.set_model (window.data.style_selection_model);

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
                    window,
                    window.data.figure_settings
                );
            });
            action_group.add_action (create_action);
            insert_action_group ("figure_settings", action_group);
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
