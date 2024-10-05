// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {
    namespace Actions {
        public void setup (Application application, Window window) {
            var data = window.data;

            var toggle_sidebar_action = new SimpleAction.stateful (
                "toggle_sidebar",
                null,
                new Variant.boolean (true)
            );
            toggle_sidebar_action.activate.connect (() => {
                OverlaySplitView split_view = window.split_view;
                split_view.collapsed = !split_view.collapsed;
            });
            window.add_action (toggle_sidebar_action);

            var modes = new ArrayList<string>.wrap ({"pan", "zoom", "select"});
            foreach (string mode in modes) {
                var action = new SimpleAction (@"mode_$mode", null);
                action.activate.connect (() => {
                    window.canvas.mode = modes.index_of (mode);
                });
                window.add_action (action);
            }

            GLib.Settings figure_settings = application.get_settings_child ("figure");
            foreach (string dir in DIRECTION_NAMES) {
                string val = @"$dir-scale";
                var action = new SimpleAction.stateful (
                    @"change-$val",
                    new VariantType ("s"),
                    new Variant.string (figure_settings.get_enum (val).to_string ())
                );
                action.activate.connect ((a, target) => {
                    string[] directions = {dir};
                    bool[] visible_axes = data.get_used_positions ();
                    // Also set opposite axis if opposite axis not in use
                    if (dir in X_DIRECTIONS && visible_axes[0] ^ visible_axes[1]) {
                        directions = X_DIRECTIONS;
                    }
                    if (dir in Y_DIRECTIONS && visible_axes[2] ^ visible_axes[3]) {
                        directions = Y_DIRECTIONS;
                    }
                    foreach (string target_dir in directions) {
                        data.figure_settings.set (
                            val, int.parse (target.get_string ())
                        );
                    }
                    data.add_history_state ();
                });
                data.figure_settings.notify[val].connect (() => {
                    int scale;
                    data.figure_settings.get (val, out scale);
                    action.set_state (new Variant.string (scale.to_string ()));
                });
                window.add_action (action);
            }

            string[] settings_actions = {"center", "smoothen"};
            GLib.Settings actions_settings = application.get_settings_child ("actions");
            foreach (string settings_action in settings_actions) {
                window.add_action (actions_settings.create_action (settings_action));
            }

            var operation_action = new SimpleAction (
                "perform_operation", new VariantType ("s")
            );
            operation_action.activate.connect ((a, target) => {
                application.operation_invoked.emit (window, target.get_string ());
            });
            window.add_action (operation_action);

            var optimize_limits_action = new SimpleAction ("optimize_limits", null);
            optimize_limits_action.activate.connect (() => {
                data.optimize_limits ();
            });
            window.add_action (optimize_limits_action);

            var smoothen_settings_action = new SimpleAction ("smoothen_settings", null);
            smoothen_settings_action.activate.connect (() => {
                new SmoothenDialog (window);
            });
            window.add_action (smoothen_settings_action);

            var select_all_action = new SimpleAction ("select_all", null);
            select_all_action.activate.connect (() => {
                foreach (Item item in data) {
                    item.selected = true;
                }
                data.add_history_state ();
            });
            window.add_action (select_all_action);

            var select_none_action = new SimpleAction ("select_none", null);
            select_none_action.activate.connect (() => {
                foreach (Item item in data) {
                    item.selected = false;
                }
                data.add_history_state ();
            });
            window.add_action (select_none_action);

            var undo_action = new SimpleAction ("undo", null);
            undo_action.activate.connect (() => {
                data.undo ();
            });
            window.add_action (undo_action);

            var redo_action = new SimpleAction ("redo", null);
            redo_action.activate.connect (() => {
                data.redo ();
            });
            window.add_action (redo_action);

            var view_back_action = new SimpleAction ("view_back", null);
            view_back_action.activate.connect (() => {
                data.view_back ();
            });
            window.add_action (view_back_action);

            var view_forward_action = new SimpleAction ("view_forward", null);
            view_forward_action.activate.connect (() => {
                data.view_forward ();
            });
            window.add_action (view_forward_action);

            var delete_selected_action = new SimpleAction ("delete_selected", null);
            delete_selected_action.activate.connect (() => {
                Item[] items = {};
                var name_builder = new StringBuilder ();
                foreach (Item item in data) {
                    if (item.selected) {
                        items += item;
                        name_builder.append (item.name);
                        name_builder.append (", ");
                    }
                }
                data.delete_items (items);
                string names = name_builder.free_and_steal ()[:-2];
                window.add_undo_toast (_("Deleted %s").printf (names));
            });
            window.add_action (delete_selected_action);

            var save_project_action = new SimpleAction ("save_project", null);
            save_project_action.activate.connect (() => {
                Project.save.begin (window, false);
            });
            window.add_action (save_project_action);

            var save_project_as_action = new SimpleAction ("save_project_as", null);
            save_project_as_action.activate.connect (() => {
                Project.save.begin (window, true);
            });
            window.add_action (save_project_as_action);

            var open_project_action = new SimpleAction ("open_project", null);
            open_project_action.activate.connect (() => {
                Project.open (window);
            });
            window.add_action (open_project_action);

            var add_data_action_filters = Tools.create_file_filters (
                true,
                Tools.create_file_filter (
                    C_("file-filter", "Supported files"),
                    "xy", "dat", "txt", "csv", "xrdml", "xry", "graphs"
                ),
                Tools.create_file_filter (
                    C_("file-filter", "ASCII files"),
                    "xy", "dat", "txt", "csv"
                ),
                Tools.create_file_filter (
                    C_("file-filter", "PANalytical XRDML"), "xrdml"
                ),
                Tools.create_file_filter (
                    C_("file-filter", "Leybold xry"), "xry"
                ),
                Project.get_project_file_filter ()
            );
            var add_data_action = new SimpleAction ("add_data", null);
            add_data_action.activate.connect (() => {
                var dialog = new FileDialog ();
                dialog.set_filters (add_data_action_filters);
                dialog.open_multiple.begin (window, null, (d, response) => {
                    try {
                        var files_list_model = dialog.open_multiple.end (response);
                        File[] files = {};
                        for (uint i = 0; i < files_list_model.get_n_items (); i++) {
                            files += files_list_model.get_item (i) as File;
                        }
                        application.python_helper.import_from_files (window, files);
                    } catch {}
                });
            });
            window.add_action (add_data_action);

            var export_data_action = new SimpleAction ("export_data", null);
            export_data_action.activate.connect (() => {
                Export.export_items (window);
            });
            window.add_action (export_data_action);

            var figure_settings_action = new SimpleAction ("figure_settings", null);
            figure_settings_action.activate.connect (() => {
                new FigureSettingsDialog (window, null);
            });
            window.add_action (figure_settings_action);

            var add_equation_action = new SimpleAction ("add_equation", null);
            add_equation_action.activate.connect (() => {
                new AddEquationDialog (window);
            });
            window.add_action (add_equation_action);

            var export_figure_action = new SimpleAction ("export_figure", null);
            export_figure_action.activate.connect (() => {
                new ExportFigureDialog (window);
            });
            window.add_action (export_figure_action);

            var zoom_in_action = new SimpleAction ("zoom_in", null);
            zoom_in_action.activate.connect (() => {
                window.canvas.zoom (1.15);
            });
            window.add_action (zoom_in_action);

            var zoom_out_action = new SimpleAction ("zoom_out", null);
            zoom_out_action.activate.connect (() => {
                window.canvas.zoom (1 / 1.15);
            });
            window.add_action (zoom_out_action);
        }
    }
}
