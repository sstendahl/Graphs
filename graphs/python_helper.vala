// SPDX-License-Identifier: GPL-3.0-or-later
// Python Helper - Vala Part
using Gtk;

namespace Graphs {
    public class PythonHelper : Object {
        public Application application { protected get; construct set; }

        protected signal void python_method_request (Object object, string method);
        public void run_method (Object object, string method) {
            this.python_method_request.emit (object, method);
        }

        protected signal Widget edit_item_dialog_request (Item item);
        public Widget create_edit_item_dialog (Item item) {
            return this.edit_item_dialog_request.emit (item);
        }

        protected signal CurveFittingDialog curve_fitting_dialog_request (Item item);
        public CurveFittingDialog create_curve_fitting_dialog (Item item) {
            return this.curve_fitting_dialog_request.emit (item);
        }

        protected signal bool validate_input_request (string input);
        public bool validate_input (string input) {
            return this.validate_input_request.emit (input);
        }

        protected signal void import_from_files_request (ListModel files);
        public void import_from_files (ListModel files) {
            this.import_from_files_request.emit (files);
        }

        protected signal void export_items_request (string mode, File file, Item[] items);
        public void export_items (string mode, File file, Item[] items) {
            this.export_items_request.emit (mode, file, items);
        }
    }
}
