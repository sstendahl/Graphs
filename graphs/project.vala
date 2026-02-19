// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {

    public errordomain ProjectParseError {
        INVALID_PROJECT,
        LEGACY_MIGRATION_DISALLOWED,
        BETA_DISALLOWED
    }

    [Flags]
    public enum ProjectParseFlags {
        NONE = 0,
        ALLOW_LEGACY_MIGRATION = 1 << 0,
        ALLOW_BETA = 1 << 1
    }

    namespace Project {

        public FileFilter get_project_file_filter () {
            return Tools.create_file_filter (
                C_("file-filter", "Graphs Project File"), "graphs"
            );
        }

        private void _save (Window window) {
            window.data.save ();
            window.add_toast_string_with_file (
                _("Saved Project"), window.data.file
            );
        }

        private ListModel get_project_file_filters () {
            return Tools.create_file_filters (false, get_project_file_filter ());
        }

        public async bool save (Window window, bool require_dialog) {
            if (window.data.file != null && !require_dialog) {
                _save (window);
                return true;
            }
            var dialog = new FileDialog ();
            dialog.set_filters (get_project_file_filters ());
            dialog.set_initial_name (_("Project") + ".graphs");
            try {
                window.data.file = yield dialog.save (window, null);
                _save (window);
                return true;
            } catch {
                return false;
            }
        }

        public async bool load (
            Window window, Data data, File file, ProjectParseFlags flags = ProjectParseFlags.NONE
        ) {
            try {
                data.load (file, flags);
                return true;
            } catch (ProjectParseError e) {
                // Handle warnings & general error
                string dialog_name;
                ProjectParseFlags new_flags;
                switch (e.code) {
                    case ProjectParseError.LEGACY_MIGRATION_DISALLOWED:
                        dialog_name = "legacy_migration_disallowed";
                        new_flags = flags | ProjectParseFlags.ALLOW_LEGACY_MIGRATION;
                        break;
                    case ProjectParseError.BETA_DISALLOWED:
                        dialog_name = "beta_disallowed";
                        new_flags = flags | ProjectParseFlags.ALLOW_BETA;
                        break;
                    default:
                        var error_dialog = (Adw.AlertDialog) Tools.build_dialog ("invalid_project");
                        error_dialog.set_body (e.message);
                        error_dialog.present (window);
                        return false;
                    }
                var dialog = (Adw.AlertDialog) Tools.build_dialog (dialog_name);
                var response = yield dialog.choose (window, null);
                if (response != "continue") return false;
                return yield load (window, data, file, new_flags);
            }
        }

        public async void open (Window window) {
            var dialog = new FileDialog ();
            dialog.set_filters (get_project_file_filters ());
            try {
                var file = yield dialog.open (window, null);
                if (!window.data.unsaved && window.data.file == null) {
                    yield load (window, window.data, file);
                    return;
                }

                Application application = (Application) window.application;
                Window new_window = application.create_main_window ();
                if (yield load (window, new_window.data, file)) {
                    new_window.present ();
                    return;
                };
                application.on_main_window_closed (new_window);
            } catch {}
        }

        public void close (Window window) {
            if (!window.data.unsaved) {
                window.data.clear ();
                return;
            }
            var dialog = (Adw.AlertDialog) Tools.build_dialog ("save_project_changes");
            dialog.response.connect ((d, response) => {
                switch (response) {
                    case "discard": {
                        window.data.clear ();
                        break;
                    }
                    case "save": {
                        save.begin (window, false, (o, result) => {
                            if (save.end (result)) {
                                window.data.clear ();
                            }
                        });
                        break;
                    }
                }
            });
            dialog.present (window);
        }
    }
}
