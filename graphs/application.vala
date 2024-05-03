// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;

namespace Graphs {
    private const string[] X_DIRECTIONS = {"top", "bottom"};
    private const string[] Y_DIRECTIONS = {"left", "right"};
    private const string[] PYTHON_ACTIONS = {
        "add_data",
        "add_equation",
        "export_data",
        "export_figure",
        "new_project",
        "zoom_in",
        "zoom_out",
        "figure_settings"
    };

    /**
     * Graphs application
     */
    public class Application : Adw.Application {
        public Window window { get; set; }
        public Settings settings { get; construct set; }
        public Data data { get; construct set; }
        public StyleManager figure_style_manager { get; set; }
        public bool debug { get; construct set; default = false; }
        public PythonHelper python_helper { get; construct set; }

        public signal void action_invoked (string name);
        public signal void operation_invoked (string name);

        construct {
            Intl.bindtextdomain (Config.GETTEXT_PACKAGE, Config.LOCALEDIR);
            Intl.bind_textdomain_codeset (Config.GETTEXT_PACKAGE, "UTF-8");
            Intl.textdomain (Config.GETTEXT_PACKAGE);

            this.version = Config.VERSION;
        }

        /**
         * Retrieve a child of the applications settings.
         *
         * @param path a slash-separated path
         */
        public Settings get_settings_child (string path) {
            Settings settings = this.settings;
            foreach (string child_name in path.split ("/")) {
                settings = settings.get_child (child_name);
            }
            return settings;
        }

        public bool close () {
            if (this.data.unsaved) {
                var dialog = (Adw.AlertDialog) Tools.build_dialog ("save_changes");
                dialog.response.connect ((d, response) => {
                    switch (response) {
                        case "discard_close": {
                            this.quit ();
                            break;
                        }
                        case "save_close": {
                            Project.save.begin (this, false, (o, result) => {
                                Project.save.end (result);
                                this.quit ();
                            });
                            break;
                        }
                    }
                });
                dialog.present (this.window);
                return true;
            } else {
                this.quit ();
                return false;
            }
        }

        /**
         * Setup actions.
         */
        public void setup_actions () {
            foreach (string name in PYTHON_ACTIONS) {
                var action = new SimpleAction (name, null);
                action.activate.connect (() => {
                    this.action_invoked.emit (name);
                });
                this.add_action (action);
            }
            this.set_accels_for_action ("app.help", {"F1"});

            var toggle_sidebar_action = new SimpleAction.stateful (
                "toggle_sidebar",
                null,
                new Variant.boolean (true)
            );
            toggle_sidebar_action.activate.connect (() => {
                OverlaySplitView split_view = this.window.split_view;
                split_view.collapsed = !split_view.collapsed;
            });
            this.add_action (toggle_sidebar_action);

            var modes = new ArrayList<string>.wrap ({"pan", "zoom", "select"});
            foreach (string mode in modes) {
                var action = new SimpleAction (@"mode_$mode", null);
                action.activate.connect (() => {
                    this.window.canvas.mode = modes.index_of (mode);
                });
                this.add_action (action);
            }

            Settings settings = this.get_settings_child ("figure");
            FigureSettings figure_settings = this.data.figure_settings;
            foreach (string dir in DIRECTION_NAMES) {
                string val = @"$dir-scale";
                var action = new SimpleAction.stateful (
                    @"change-$val",
                    new VariantType ("s"),
                    new Variant.string (settings.get_enum (val).to_string ())
                );
                action.activate.connect ((a, target) => {
                    string[] directions = {dir};
                    bool[] visible_axes = this.data.get_used_positions ();
                    // Also set opposite axis if opposite axis not in use
                    if (dir in X_DIRECTIONS && visible_axes[0] ^ visible_axes[1]) {
                        directions = X_DIRECTIONS;
                    }
                    if (dir in Y_DIRECTIONS && visible_axes[2] ^ visible_axes[3]) {
                        directions = Y_DIRECTIONS;
                    }
                    foreach (string target_dir in directions) {
                        figure_settings.set (
                            val, int.parse (target.get_string ())
                        );
                    }
                    this.data.add_history_state ();
                });
                figure_settings.notify[val].connect (() => {
                    int scale;
                    figure_settings.get (val, out scale);
                    action.set_state (new Variant.string (scale.to_string ()));
                });
                this.add_action (action);
            }

            string[] settings_actions = {"center", "smoothen"};
            Settings actions_settings = this.settings.get_child ("actions");
            foreach (string settings_action in settings_actions) {
                this.add_action (actions_settings.create_action (settings_action));
            }

            var operation_action = new SimpleAction (
                "app.perform_operation", new VariantType ("s")
            );
            operation_action.activate.connect ((a, target) => {
                this.operation_invoked.emit (target.get_string ());
            });
            this.add_action (operation_action);

            var quit_action = new SimpleAction ("quit", null);
            quit_action.activate.connect (() => {
                this.close ();
            });
            this.add_action (quit_action);

            var about_action = new SimpleAction ("about", null);
            about_action.activate.connect (() => {
                show_about_dialog (this);
            });
            this.add_action (about_action);

            var help_action = new SimpleAction ("help", null);
            help_action.activate.connect (() => {
                try {
                    AppInfo.launch_default_for_uri (
                        "help:graphs",
                        this.window.get_display ().get_app_launch_context ()
                    );
                } catch { assert_not_reached (); }
            });
            this.add_action (help_action);

            var optimize_limits_action = new SimpleAction ("optimize_limits", null);
            optimize_limits_action.activate.connect (() => {
                this.data.optimize_limits ();
            });
            this.add_action (optimize_limits_action);

            var smoothen_settings_action = new SimpleAction ("smoothen_settings", null);
            smoothen_settings_action.activate.connect (() => {
                new SmoothenDialog (this);
            });
            this.add_action (smoothen_settings_action);

            var select_all_action = new SimpleAction ("select_all", null);
            select_all_action.activate.connect (() => {
                foreach (Item item in this.data) {
                    item.selected = true;
                }
                this.data.add_history_state ();
            });
            this.add_action (select_all_action);

            var select_none_action = new SimpleAction ("select_none", null);
            select_none_action.activate.connect (() => {
                foreach (Item item in this.data) {
                    item.selected = false;
                }
                this.data.add_history_state ();
            });
            this.add_action (select_none_action);

            var undo_action = new SimpleAction ("undo", null);
            undo_action.activate.connect (() => {
                this.data.undo ();
            });
            this.add_action (undo_action);

            var redo_action = new SimpleAction ("redo", null);
            redo_action.activate.connect (() => {
                this.data.redo ();
            });
            this.add_action (redo_action);

            var view_back_action = new SimpleAction ("view_back", null);
            view_back_action.activate.connect (() => {
                this.data.view_back ();
            });
            this.add_action (view_back_action);

            var view_forward_action = new SimpleAction ("view_forward", null);
            view_forward_action.activate.connect (() => {
                this.data.view_forward ();
            });
            this.add_action (view_forward_action);

            var delete_selected_action = new SimpleAction ("delete_selected", null);
            delete_selected_action.activate.connect (() => {
                Item[] items = {};
                var name_builder = new StringBuilder ();
                foreach (Item item in this.data) {
                    if (item.selected) {
                        items += item;
                        name_builder.append (item.name);
                        name_builder.append (", ");
                    }
                }
                string names = name_builder.free_and_steal ()[:-2];
                var toast = new Adw.Toast (_("Deleted %s").printf (names));
                toast.set_button_label (_("Undo"));
                toast.set_action_name ("app.undo");
                this.data.delete_items (items);
                this.window.add_toast (toast);
            });
            this.add_action (delete_selected_action);

            var save_project_action = new SimpleAction ("save_project", null);
            save_project_action.activate.connect (() => {
                Project.save.begin (this, false);
            });
            this.add_action (save_project_action);

            var save_project_as_action = new SimpleAction ("save_project_as", null);
            save_project_as_action.activate.connect (() => {
                Project.save.begin (this, true);
            });
            this.add_action (save_project_as_action);

            var open_project_action = new SimpleAction ("open_project", null);
            open_project_action.activate.connect (() => {
                Project.open (this);
            });
            this.add_action (open_project_action);
        }
    }
}
