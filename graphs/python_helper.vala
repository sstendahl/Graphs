// SPDX-License-Identifier: GPL-3.0-or-later
// Python Helper - Vala Part
using Gtk;

namespace Graphs {
    public class PythonHelper : Object {
        public Application application { protected get; construct set; }

        private static PythonHelper instance;
        protected static void set_instance (PythonHelper instance) {
            PythonHelper.instance = instance;
        }

        protected signal Item add_equation_request (Window window, string equation, string name);
        public static Item add_equation (Window window,  string equation, string name) {
            return instance.add_equation_request.emit (window, equation, name);
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

        protected signal Item generate_data_request (Window window, string name);
        public static Item generate_data (Window window, string name) {
            return instance.generate_data_request.emit (window, name);
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
                string preprocessed = preprocess_equation (input);
                return instance.validate_equation_request.emit (preprocessed);
            } catch (MathError e) {
                return false;
            }
        }
    }
}
