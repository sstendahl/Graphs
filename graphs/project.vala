// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    namespace Project {

        public FileFilter get_project_file_filter () {
            return Tools.create_file_filter (
                C_("file-filter", "Graphs Project File"), "graphs"
            );
        }

        private void _save (Application application) {
            application.data.save ();
            application.window.add_toast_string_with_file (
                _("Saved Project"), application.data.file
            );
        }

        private ListModel get_project_file_filters () {
            return Tools.create_file_filters (false, get_project_file_filter ());
        }

        public async bool save (Application application, bool require_dialog) {
            if (application.data.file != null && !require_dialog) {
                _save (application);
                return true;
            }
            var dialog = new FileDialog ();
            dialog.set_filters (get_project_file_filters ());
            dialog.set_initial_name (_("Project") + ".graphs");
            try {
                application.data.file = yield dialog.save (application.window, null);
                _save (application);
                return true;
            } catch {
                return false;
            }
        }

        private void _pick_and_load (Application application) {
            var dialog = new FileDialog ();
            dialog.set_filters (get_project_file_filters ());
            dialog.open.begin (application.window, null, (d, response) => {
                try {
                    application.data.file = dialog.open.end (response);
                    application.data.load ();
                } catch {}
            });
        }

        public void open (Application application) {
            if (!application.data.unsaved) {
                _pick_and_load (application);
                return;
            }
            var dialog = Tools.build_dialog ("save_changes") as Adw.AlertDialog;
            dialog.response.connect ((d, response) => {
                switch (response) {
                    case "discard_close": {
                        _pick_and_load (application);
                        break;
                    }
                    case "save_close": {
                        save.begin (application, false, (o, result) => {
                            save.end (result);
                            _pick_and_load (application);
                        });
                        break;
                    }
                }
            });
            dialog.present (application.window);
        }

        public void @new (Application application) {
            if (!application.data.unsaved) {
                application.data.reset ();
                return;
            }
            var dialog = Tools.build_dialog ("save_changes") as Adw.AlertDialog;
            dialog.response.connect ((d, response) => {
                switch (response) {
                    case "discard_close": {
                        application.data.reset ();
                        break;
                    }
                    case "save_close": {
                        save.begin (application, false, (o, result) => {
                            save.end (result);
                            application.data.reset ();
                        });
                        break;
                    }
                }
            });
            dialog.present (application.window);
        }
    }
}
