// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {
    namespace Actions {
        public void setup_global (Application application) {
            var quit_action = new SimpleAction ("quit", null);
            quit_action.activate.connect (application.quit_action);
            application.add_action (quit_action);
            application.set_accels_for_action ("app.quit", {"<control>q"});

            var about_action = new SimpleAction ("about", null);
            about_action.activate.connect (() => {
                var file = File.new_for_uri ("resource:///se/sjoerd/Graphs/whats_new");
                string release_notes;
                try {
                    release_notes = (string) file.load_bytes ().get_data ();
                } catch {
                    release_notes = "";
                }

                var dialog = new Adw.AboutDialog () {
                    application_name = _("Graphs"),
                    application_icon = application.application_id,
                    website = Config.HOMEPAGE_URL,
                    developer_name = _("The Graphs Developers"),
                    issue_url = Config.ISSUE_URL,
                    version = application.version,
                    developers = {
                        "Sjoerd Stendahl <contact@sjoerd.se>",
                        "Christoph Matthias Kohnen <mail@cmkohnen.de>"
                    },
                    designers = {
                        "Sjoerd Stendahl <contact@sjoerd.se>",
                        "Christoph Matthias Kohnen <mail@cmkohnen.de>",
                        "Tobias Bernard <tbernard@gnome.org>"
                    },
                    copyright = "© " + Config.COPYRIGHT,
                    license_type = License.GPL_3_0,
                    translator_credits = _("translator-credits"),
                    release_notes = release_notes
                };
                dialog.present (application.active_window);
            });
            application.add_action (about_action);

            var help_action = new SimpleAction ("help", null);
            help_action.activate.connect (() => {
                try {
                    AppInfo.launch_default_for_uri (
                        "help:graphs",
                        application.active_window.get_display ().get_app_launch_context ()
                    );
                } catch { assert_not_reached (); }
            });
            application.add_action (help_action);
            application.set_accels_for_action ("app.help", {"F1"});

            var new_window_action = new SimpleAction ("new-window", null);
            new_window_action.activate.connect (() => {
                var window = application.create_main_window ();
                window.present ();
            });
            application.add_action (new_window_action);

            var style_editor_action = new SimpleAction ("style-editor", null);
            style_editor_action.activate.connect (() => {
                var style_editor = application.create_style_editor ();
                style_editor.present ();
            });
            application.add_action (style_editor_action);
        }

        public void setup_local (Window window) {
            var application = window.application as Application;
            var data = window.data;

            var toggle_sidebar_action = new SimpleAction ("toggle-sidebar", null);
            toggle_sidebar_action.activate.connect (() => {
                OverlaySplitView split_view = window.overlay_split_view;
                split_view.show_sidebar = !split_view.show_sidebar;
            });
            window.overlay_split_view.bind_property (
                "collapsed",
                toggle_sidebar_action,
                "enabled",
                BindingFlags.SYNC_CREATE
            );
            window.add_action (toggle_sidebar_action);

            var modes = new ArrayList<string>.wrap ({"pan", "zoom", "select"});
            foreach (string mode in modes) {
                var action = new SimpleAction (@"mode-$mode", null);
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
                application.python_helper.perform_operation (window, target.get_string ());
            });
            window.add_action (operation_action);

            var optimize_limits_action = new SimpleAction ("optimize-limits", null);
            optimize_limits_action.activate.connect (() => {
                data.optimize_limits ();
            });
            window.add_action (optimize_limits_action);

            var smoothen_settings_action = new SimpleAction ("smoothen-settings", null);
            smoothen_settings_action.activate.connect (() => {
                new SmoothenDialog (window);
            });
            window.add_action (smoothen_settings_action);

            var select_all_action = new SimpleAction ("select-all", null);
            select_all_action.activate.connect (() => {
                data.select_all ();
                data.add_history_state ();
            });
            window.add_action (select_all_action);

            var select_none_action = new SimpleAction ("select-none", null);
            select_none_action.activate.connect (() => {
                data.unselect_all ();
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

            var view_back_action = new SimpleAction ("view-back", null);
            view_back_action.activate.connect (() => {
                data.view_back ();
                window.canvas.view_action ();
            });
            window.add_action (view_back_action);

            var view_forward_action = new SimpleAction ("view-forward", null);
            view_forward_action.activate.connect (() => {
                data.view_forward ();
                window.canvas.view_action ();
            });
            window.add_action (view_forward_action);

            var delete_selected_action = new SimpleAction ("delete-selected", null);
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

            var save_project_action = new SimpleAction ("save-project", null);
            save_project_action.activate.connect (() => {
                Project.save.begin (window, false);
            });
            save_project_action.set_enabled (false);
            window.add_action (save_project_action);

            var save_project_as_action = new SimpleAction ("save-project-as", null);
            save_project_as_action.activate.connect (() => {
                Project.save.begin (window, true);
            });
            save_project_as_action.set_enabled (false);
            window.add_action (save_project_as_action);

            var open_project_action = new SimpleAction ("open-project", null);
            open_project_action.activate.connect (() => {
                Project.open (window);
            });
            window.add_action (open_project_action);

            var close_project_action = new SimpleAction ("close-project", null);
            close_project_action.activate.connect (() => {
                Project.close (window);
            });
            close_project_action.set_enabled (false);
            window.add_action (close_project_action);

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
            var add_data_action = new SimpleAction ("add-data", null);
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

            var export_data_action = new SimpleAction ("export-data", null);
            export_data_action.activate.connect (() => {
                Export.export_items (window);
            });
            window.add_action (export_data_action);

            var figure_settings_action = new SimpleAction ("figure-settings", null);
            figure_settings_action.activate.connect (() => {
                new FigureSettingsDialog (window, null);
            });
            window.add_action (figure_settings_action);

            var add_equation_action = new SimpleAction ("add-equation", null);
            add_equation_action.activate.connect (() => {
                new AddEquationDialog (window);
            });
            window.add_action (add_equation_action);

            var generate_data_action = new SimpleAction ("generate-data", null);
            generate_data_action.activate.connect (() => {
                new GenerateDataDialog (window);
            });
            window.add_action (generate_data_action);

            var export_figure_action = new SimpleAction ("export-figure", null);
            export_figure_action.activate.connect (() => {
                new ExportFigureDialog (window);
            });
            window.add_action (export_figure_action);

            var zoom_in_action = new SimpleAction ("zoom-in", null);
            zoom_in_action.activate.connect (() => {
                window.canvas.zoom (1.15);
            });
            window.add_action (zoom_in_action);

            var zoom_out_action = new SimpleAction ("zoom-out", null);
            zoom_out_action.activate.connect (() => {
                window.canvas.zoom (1 / 1.15);
            });
            window.add_action (zoom_out_action);
        }
    }
}
