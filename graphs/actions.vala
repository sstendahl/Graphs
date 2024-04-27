// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;

namespace Graphs {
    private const string[] X_DIRECTIONS = {"top", "bottom"};
    private const string[] Y_DIRECTIONS = {"left", "right"};

    /**
     * Setup actions.
     *
     * @param application Application
     */
    public void setup_actions (Application application) {
        foreach (string name in ACTION_NAMES) {
            var action = new SimpleAction (name, null);
            action.activate.connect (() => {
                application.action_invoked.emit (name);
            });
            application.add_action (action);
        }
        application.set_accels_for_action ("app.help", {"F1"});

        var toggle_sidebar_action = new SimpleAction.stateful (
            "toggle_sidebar",
            null,
            new Variant.boolean (true)
        );
        toggle_sidebar_action.activate.connect (() => {
            OverlaySplitView split_view = application.window.split_view;
            split_view.collapsed = !split_view.collapsed;
        });
        application.add_action (toggle_sidebar_action);

        var modes = new ArrayList<string>.wrap ({"pan", "zoom", "select"});
        foreach (string mode in modes) {
            var action = new SimpleAction (@"mode_$mode", null);
            action.activate.connect (() => {
                application.window.canvas.mode = modes.index_of (mode);
            });
            application.add_action (action);
        }

        Settings settings = application.get_settings_child ("figure");
        FigureSettings figure_settings = application.data.figure_settings;
        foreach (string dir in DIRECTION_NAMES) {
            string val = @"$dir-scale";
            var action = new SimpleAction.stateful (
                @"change-$val",
                new VariantType ("s"),
                new Variant.string (settings.get_enum (val).to_string ())
            );
            action.activate.connect ((a, target) => {
                string[] directions = {dir};
                bool[] visible_axes = application.data.get_used_positions ();
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
                application.data.add_history_state ();
            });
            figure_settings.notify[val].connect (() => {
                int scale;
                figure_settings.get (val, out scale);
                action.set_state (new Variant.string (scale.to_string ()));
            });
            application.add_action (action);
        }

        string[] settings_actions = {"center", "smoothen"};
        Settings actions_settings = application.settings.get_child ("actions");
        foreach (string settings_action in settings_actions) {
            application.add_action (actions_settings.create_action (settings_action));
        }

        var operation_action = new SimpleAction (
            "app.perform_operation", new VariantType ("s")
        );
        operation_action.activate.connect ((a, target) => {
            application.operation_invoked.emit (target.get_string ());
        });
        application.add_action (operation_action);

        var quit_action = new SimpleAction ("quit", null);
        quit_action.activate.connect (() => {
            application.close ();
        });
        application.add_action (quit_action);

        var about_action = new SimpleAction ("about", null);
        about_action.activate.connect (() => {
            show_about_dialog (application);
        });
        application.add_action (about_action);

        var help_action = new SimpleAction ("help", null);
        help_action.activate.connect (() => {
            try {
                AppInfo.launch_default_for_uri (
                    "help:graphs",
                    application.window.get_display ().get_app_launch_context ()
                );
            } catch { assert_not_reached (); }
        });
        application.add_action (help_action);

        var optimize_limits_action = new SimpleAction ("optimize_limits", null);
        optimize_limits_action.activate.connect (() => {
            application.data.optimize_limits ();
        });
        application.add_action (optimize_limits_action);

        var smoothen_settings_action = new SimpleAction ("smoothen_settings", null);
        smoothen_settings_action.activate.connect (() => {
            new SmoothenDialog (application);
        });
        application.add_action (smoothen_settings_action);

        var select_all_action = new SimpleAction ("select_all", null);
        select_all_action.activate.connect (() => {
            foreach (Item item in application.data) {
                item.selected = true;
            }
            application.data.add_history_state ();
        });
        application.add_action (select_all_action);

        var select_none_action = new SimpleAction ("select_none", null);
        select_none_action.activate.connect (() => {
            foreach (Item item in application.data) {
                item.selected = false;
            }
            application.data.add_history_state ();
        });
        application.add_action (select_none_action);

        var undo_action = new SimpleAction ("undo", null);
        undo_action.activate.connect (() => {
            application.data.undo ();
        });
        application.add_action (undo_action);

        var redo_action = new SimpleAction ("redo", null);
        redo_action.activate.connect (() => {
            application.data.redo ();
        });
        application.add_action (redo_action);

        var view_back_action = new SimpleAction ("view_back", null);
        view_back_action.activate.connect (() => {
            application.data.view_back ();
        });
        application.add_action (view_back_action);

        var view_forward_action = new SimpleAction ("view_forward", null);
        view_forward_action.activate.connect (() => {
            application.data.view_forward ();
        });
        application.add_action (view_forward_action);

        var delete_selected_action = new SimpleAction ("delete_selected", null);
        delete_selected_action.activate.connect (() => {
            Item[] items = {};
            var name_builder = new StringBuilder ();
            foreach (Item item in application.data) {
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
            application.data.delete_items (items);
            application.window.add_toast (toast);
        });
        application.add_action (delete_selected_action);

        var figure_settings_action = new SimpleAction ("figure_settings", null);
        figure_settings_action.activate.connect (() => {
            application.python_helper.create_figure_settings_dialog ();
        });
        application.add_action (figure_settings_action);
    }
}
