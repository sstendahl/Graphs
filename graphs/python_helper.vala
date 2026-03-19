// SPDX-License-Identifier: GPL-3.0-or-later
// Python Helper - Vala Part
using Gtk;

namespace Graphs {
    public class PythonHelper : Object {
        private static PythonHelper instance;

        construct {
            instance = this;
        }

        protected signal EquationItem add_equation_request (Data data, string equation, string name);
        public static EquationItem add_equation (Data data, string equation, string name) {
            return instance.add_equation_request.emit (data, equation, name);
        }

        protected signal StyleEditor create_style_editor_request ();
        public static StyleEditor create_style_editor () {
            return instance.create_style_editor_request.emit ();
        }

        protected signal Window create_window_request ();
        public static Window create_window () {
            return instance.create_window_request ();
        }

        protected signal CurveFittingDialog curve_fitting_dialog_request (Window window, Item item);
        public static CurveFittingDialog create_curve_fitting_dialog (Window window, Item item) {
            return instance.curve_fitting_dialog_request.emit (window, item);
        }

        protected signal void export_items_request (Window window, string mode, File file, Item[] items);
        public static void export_items (Window window, string mode, File file, Item[] items) {
            instance.export_items_request.emit (window, mode, file, items);
            window.add_toast_string_with_file (
                _("Exported Data"), file
            );
        }

        public signal void export_figure_request (File file, GLib.Settings settings, Data data);
        public static void export_figure (File file, GLib.Settings settings, Data data) {
            instance.export_figure_request.emit (file, settings, data);
        }

        protected signal int has_err_request (Item item);
        public static void item_has_err (Item item, out bool xerr, out bool yerr) {
            int result = instance.has_err_request.emit (item);
            xerr = result == 1 || result == 3;
            yerr = result == 2 || result == 3;
        }

        protected signal GeneratedDataItem generate_data_request (Data data, string name);
        public static GeneratedDataItem generate_data (Data data, string name) {
            return instance.generate_data_request.emit (data, name);
        }

        protected signal void perform_operation_request (Window window, string name);
        public static void perform_operation (Window window, string name) {
            instance.perform_operation_request.emit (window, name);
        }

        protected signal void python_method_request (Object object, string method);
        public static void run_method (Object object, string method) {
            instance.python_method_request.emit (object, method);
        }

        protected signal string simplify_equation_request (string input);
        public static string simplify_equation (string input) {
            return instance.simplify_equation_request.emit (input);
        }

        protected signal bool validate_equation_request (string input);
        public static bool validate_equation (string input) {
            try {
                return instance.validate_equation_request.emit (preprocess_equation (input));
            } catch (MathError e) {
                return false;
            }
        }
    }
}
