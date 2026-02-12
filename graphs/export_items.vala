// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;

namespace Graphs {
    namespace Export {
        public void export_items (Window window) {
            Data data = window.data;
            if (data.is_empty ()) {
                window.add_toast_string (_("No data to export"));
                return;
            }

            var dialog = new FileDialog ();
            if (data.get_n_items () > 1) {
                dialog.select_folder.begin (window, null, (d, response) => {
                    try {
                        PythonHelper.export_items (
                            window,
                            "columns",
                            dialog.select_folder.end (response),
                            data.get_items ()
                        );
                    } catch {}
                });
            } else {
                Item item = data.get_item (0) as Item;
                dialog.set_initial_name (item.name + ".txt");
                dialog.set_filters (Tools.create_file_filters (
                    true,
                    Tools.create_file_filter (
                        C_("file-filter", "Text Files"), "txt"
                    )
                ));
                dialog.save.begin (window, null, (d, response) => {
                    try {
                        PythonHelper.export_items (
                            window,
                            "columns",
                            dialog.save.end (response),
                            data.get_items ()
                        );
                    } catch {}
                });
            }
        }
    }
}
