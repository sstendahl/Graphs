// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {

    public errordomain ProjectParseError {
        INVALID_PROJECT
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

        private void _pick_and_load (Window window) {
            var dialog = new FileDialog ();
            dialog.set_filters (get_project_file_filters ());
            dialog.open.begin (window, null, (d, response) => {
                try {
                    var file = dialog.open.end (response);
                    window.data.load (file);
                } catch (ProjectParseError e) {
                    window.add_toast_string (e.message);
                } catch {}
            });
        }

        public void open (Window window) {
            if (!window.data.unsaved && window.data.file == null) {
                _pick_and_load (window);
                return;
            }
            Application application = window.application as Application;
            var new_window = application.create_main_window ();
            new_window.present ();
            _pick_and_load (new_window);
        }
    }
}
