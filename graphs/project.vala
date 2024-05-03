// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;

namespace Graphs {
    namespace Project {

        private void _save (Application application) {
            application.data.save ();
            application.window.add_toast_string_with_file (
                _("Saved Project"), application.data.file
            );
        }

        private ListModel get_project_file_filters () {
            var list_store = new GLib.ListStore (typeof (FileFilter));
            var filter = new FileFilter ();
            filter.set_filter_name (C_("file-filter", "Graphs Project File"));
            filter.add_suffix ("graphs");
            list_store.append (filter);
            return list_store;
        }

        public void save (Application application, bool require_dialog) {
            if (application.data.file != null && !require_dialog) {
                _save (application);
                return;
            }
            var dialog = new FileDialog ();
            dialog.set_filters (get_project_file_filters ());
            dialog.set_initial_name (_("Project") + ".graphs");
            dialog.save.begin (application.window, null, (d, response) => {
                try {
                    application.data.file = dialog.save.end (response);
                    _save (application);
                } catch {}
            });
        }

    }
}
