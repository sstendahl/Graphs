// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;

namespace Graphs {
    private const string[] X_DIRECTIONS = {"top", "bottom"};
    private const string[] Y_DIRECTIONS = {"left", "right"};

    public void setup_actions (Application application) {
        foreach (string name in ACTION_NAMES) {
            SimpleAction action = new SimpleAction (name, null);
            action.activate.connect (() => {
                application.action_invoked.emit (name);
            });
            application.add_action (action);
        }
        application.set_accels_for_action ("app.help", {"F1"});

        SimpleAction toggle_sidebar_action = new SimpleAction.stateful (
            "toggle_sidebar",
            null,
            new Variant.boolean (true)
        );
        toggle_sidebar_action.activate.connect (() => {
            OverlaySplitView split_view = application.window.split_view;
            split_view.collapsed = !split_view.collapsed;
        });
        application.add_action (toggle_sidebar_action);

        Gee.List<string> modes = new ArrayList<string>.wrap ({"pan", "zoom", "select"});
        foreach (string mode in modes) {
            SimpleAction action = new SimpleAction (@"mode_$mode", null);
            action.activate.connect (() => {
                application.mode = modes.index_of (mode);
            });
            application.add_action (action);
        }

        Settings settings = application.get_settings_child ("figure");
        FigureSettings figure_settings = application.data.figure_settings;
        foreach (string dir in DIRECTION_NAMES) {
            string val = @"$dir-scale";
            SimpleAction action = new SimpleAction.stateful (
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
                application.data.add_history_state_request.emit ();
            });
            figure_settings.notify[val].connect (() => {
                int scale;
                figure_settings.get (val, out scale);
                action.change_state (new Variant.string (scale.to_string ()));
            });
            application.add_action (action);
        }

        string[] settings_actions = {"center", "smoothen"};
        Settings actions_settings = application.settings.get_child ("actions");
        foreach (string settings_action in settings_actions) {
            application.add_action (actions_settings.create_action (settings_action));
        }

        SimpleAction operation_action = new SimpleAction (
            "app.perform_operation", new VariantType ("s")
        );
        operation_action.activate.connect ((a, target) => {
            application.operation_invoked.emit (target.get_string ());
        });
        application.add_action (operation_action);
    }
}
