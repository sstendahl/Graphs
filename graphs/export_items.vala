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
                        File file = dialog.select_folder.end (response);
                        foreach (Item item in data) {
                            File item_file = file.get_child_for_display_name (item.name + ".txt");
                            save_item_as_columns (item, item_file, data.figure_settings);
                        }
                        window.add_toast_string_with_file (_("Exported Data"), file);
                    } catch {}
                });
            } else {
                Item item = (Item) data.get_item (0);
                dialog.set_initial_name (item.name + ".txt");
                dialog.set_filters (Tools.create_file_filters (
                    true,
                    Tools.create_file_filter (
                        C_("file-filter", "Text Files"), "txt"
                    )
                ));
                dialog.save.begin (window, null, (d, response) => {
                    try {
                        File file = dialog.save.end (response);
                        save_item_as_columns ((Item) data.get_item (0), file, data.figure_settings);
                        window.add_toast_string_with_file (_("Exported Data"), file);
                    } catch {}
                });
            }
        }

        private const char COLUMNS_DELIMITER = '\t';
        private const string COLUMNS_VALUE_FORMAT = "%.12e";

        private void save_item_as_columns (Item item, File file, FigureSettings figure_settings) throws Error {
            DataHolder data;
            if (item is DataItem) {
                var data_item = (DataItem) item;
                data = data_item.data;
            } else if (item is EquationItem) {
                double low, high;
                if (item.xposition == XPosition.BOTTOM) {
                    low = figure_settings.min_bottom;
                    high = figure_settings.max_bottom;
                } else {
                    low = figure_settings.min_top;
                    high = figure_settings.max_top;
                }
                data = MathTools.equation_to_data (item.equation, low, high);
            } else return;

            var stream = file.replace (null, false, FileCreateFlags.NONE, null);
            var data_stream = new DataOutputStream (stream);

            unowned var xdata = data.get_xdata ();
            unowned var ydata = data.get_ydata ();
            unowned var xerr = data.get_xerr ();
            unowned var yerr = data.get_yerr ();

            if (item.xlabel != "" && item.ylabel != "") {
                data_stream.put_string (item.xlabel);
                data_stream.put_byte (COLUMNS_DELIMITER);
                data_stream.put_string (item.ylabel);
                if (xerr != null) {
                    data_stream.put_byte (COLUMNS_DELIMITER);
                    data_stream.put_string ("x_err");
                }
                if (yerr != null) {
                    data_stream.put_byte (COLUMNS_DELIMITER);
                    data_stream.put_string ("y_err");
                }
                data_stream.put_byte ('\n');
            }

            for (uint i = 0; i < xdata.length; i++) {
                data_stream.put_string (COLUMNS_VALUE_FORMAT.printf (xdata[i]));
                data_stream.put_byte (COLUMNS_DELIMITER);
                data_stream.put_string (COLUMNS_VALUE_FORMAT.printf (ydata[i]));
                if (xerr != null) {
                    data_stream.put_byte (COLUMNS_DELIMITER);
                    data_stream.put_string (COLUMNS_VALUE_FORMAT.printf (xerr[i]));
                }
                if (yerr != null) {
                    data_stream.put_byte (COLUMNS_DELIMITER);
                    data_stream.put_string (COLUMNS_VALUE_FORMAT.printf (yerr[i]));
                }
                data_stream.put_byte ('\n');
            }

            data_stream.close ();
        }
    }
}
