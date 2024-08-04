// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;

namespace Graphs {
    namespace Export {
        public void export_items (Application application) {
            if (application.data.is_empty ()) {
                application.window.add_toast_string (_("No data to export"));
                return;
            }

            var dialog = new FileDialog ();
            if (application.data.get_n_items () > 1) {
                dialog.select_folder.begin (application.window, null, (d, response) => {
                    try {
                        application.python_helper.export_items (
                            "columns",
                            dialog.select_folder.end (response),
                            application.data.get_items ()
                        );
                    } catch {}
                });
            } else {
                Item item = application.data.get_item (0) as Item;
                dialog.set_initial_name (item.name + ".txt");
                dialog.set_filters (Tools.create_file_filters (
                    true,
                    Tools.create_file_filter (
                        C_("file-filter", "Text Files"), "txt"
                    )
                ));
                dialog.save.begin (application.window, null, (d, response) => {
                    try {
                        application.python_helper.export_items (
                            "columns",
                            dialog.save.end (response),
                            application.data.get_items ()
                        );
                    } catch {}
                });
            }
        }
    }
}
