// SPDX-License-Identifier: GPL-3.0-or-later
// Python Helper - Vala Part
using Gtk;

namespace Graphs {
    public class PythonHelper : Object {
        public Application application { protected get; construct set; }

        protected signal void python_method_request (Object object, string method);
        public void run_method (Object object, string method) {
            python_method_request.emit (object, method);
        }

        protected signal Widget edit_item_dialog_request (Item item);
        public Widget create_edit_item_dialog (Item item) {
            return edit_item_dialog_request.emit (item);
        }

        protected signal CurveFittingDialog curve_fitting_dialog_request (Item item);
        public CurveFittingDialog create_curve_fitting_dialog (Item item) {
            return curve_fitting_dialog_request.emit (item);
        }

        // Returning a double/float in a signal has issues, so we work around by
        // setting a property on the python side
        protected double evaluate_string_helper { get; set; }
        protected signal bool evaluate_string_request (string input);
        public double? evaluate_string (string input) {
            if (evaluate_string_request.emit (input)) {
                return this.evaluate_string_helper;
            } else return null;
        }
        protected double validate_equation_helper { get; set; }
        protected signal bool validate_equation_request (string input);
        public double? validate_equation (string input) {
            if (validate_equation_request.emit (input)) {
                return this.validate_equation_helper;
            } else return null;
        }

        protected signal void import_from_files_request (File[] files);
        public void import_from_files (File[] files) {
            import_from_files_request.emit (files);
        }

        protected signal void export_items_request (string mode, File file, Item[] items);
        public void export_items (string mode, File file, Item[] items) {
            export_items_request.emit (mode, file, items);
        }

        protected signal string add_equation_request (string name);
        public string add_equation (string name) {
            return add_equation_request.emit (name);
        }

        protected signal void open_style_editor_request (File file);
        public void open_style_editor (File file) {
            open_style_editor_request.emit (file);
        }
    }
}
