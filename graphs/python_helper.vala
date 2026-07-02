// SPDX-License-Identifier: GPL-3.0-or-later
// Python Helper - Vala Part
namespace Graphs {
    public class PythonHelper : Object {
        private static PythonHelper instance;

        construct {
            instance = this;
        }

        protected signal Canvas create_canvas_request (StyleParameters parameters, ListModel items, bool interactive, FigureSettings? figure_settings);
        public static Canvas create_canvas (StyleParameters parameters, ListModel items, bool interactive = false, FigureSettings? figure_settings = null) {
            return instance.create_canvas_request.emit (parameters, items, interactive, figure_settings);
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

        public signal void export_figure_request (File file, GLib.Settings settings, Data data);
        public static void export_figure (File file, GLib.Settings settings, Data data) {
            instance.export_figure_request.emit (file, settings, data);
        }

        public signal bool has_singularities_request (Expression equation, double xstart, double xstop);
        public static bool has_singularities (Expression equation, double xstart, double xstop) {
            return instance.has_singularities_request.emit (equation, xstart, xstop);
        }

        protected signal void perform_operation_request (Window window, string name);
        public static void perform_operation (Window window, string name) {
            instance.perform_operation_request.emit (window, name);
        }

        protected signal void python_method_request (Object object, string method);
        public static void run_method (Object object, string method) {
            instance.python_method_request.emit (object, method);
        }

        protected signal string simplify_expression_request (Expression input);
        public static Expression simplify_expression (Expression input) {
            try {
                return expression_to_ast (instance.simplify_expression_request.emit (input));
            } catch (MathError e) { assert_not_reached (); }
        }
    }
}
