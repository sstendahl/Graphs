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

        public async void load (Window window, File file, ProjectParseFlags flags = ProjectParseFlags.NONE) throws ProjectParseError{
            try {
                window.data.load (file, flags);
            } catch (ProjectParseError e) {
                if (e is ProjectParseError.LEGACY_MIGRATION_DISALLOWED) {
                    var dialog = Tools.build_dialog ("legacy_migration_disallowed") as Adw.AlertDialog;
                    dialog.present (window);
                    var response = yield dialog.choose (window, null);
                    if (response != "continue") return;
                    yield load (window, file, flags | ProjectParseFlags.ALLOW_LEGACY_MIGRATION);
                } else if (e is ProjectParseError.BETA_DISALLOWED) {
                    var dialog = Tools.build_dialog ("beta_disallowed") as Adw.AlertDialog;
                    dialog.present (window);
                    var response = yield dialog.choose (window, null);
                    if (response != "continue") return;
                    yield load (window, file, flags | ProjectParseFlags.ALLOW_BETA);
                } else {
                    throw e;
                }
            }
        }

        public void open (Window window) {
            var dialog = new FileDialog ();
            dialog.set_filters (get_project_file_filters ());
            dialog.open.begin (window, null, (d, response) => {
                Window? new_window = null;
                Application application = window.application as Application;
                try {
                    var file = dialog.open.end (response);
                    if (!window.data.unsaved && window.data.file == null) {
                        load.begin (window, file);
                        return;
                    }
                    new_window = application.create_main_window ();
                    new_window.present ();
                    load.begin (new_window, file);
                } catch (ProjectParseError e) {
                    var error_dialog = Tools.build_dialog ("invalid_project") as Adw.AlertDialog;
                    error_dialog.set_body (e.message);
                    error_dialog.present (window);
                    if (new_window != null) {
                        new_window.close ();
                        application.on_main_window_closed (new_window);
                    }
                } catch {}
            });
        }

        public void close (Window window) {
            if (!window.data.unsaved) {
                window.data.clear ();
                return;
            }
            var dialog = Tools.build_dialog ("save_project_changes") as Adw.AlertDialog;
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
