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

        protected signal Window create_window_request ();
        public static Window create_window () {
            return instance.create_window_request ();
        }

        protected signal CurveFittingError curve_fit_request (FitProblem problem, FitResult result);
        public static CurveFittingError curve_fit (FitProblem problem, FitResult result) {
            return instance.curve_fit_request.emit (problem, result);
        }

        public signal void copy_figure_request (Data data, int width, int height);
        public static void copy_figure (Data data, int width, int height) {
            instance.copy_figure_request.emit (data, width, height);
        }

        public signal void export_figure_request (File file, Settings settings, Data data);
        public static void export_figure (File file, Settings settings, Data data) {
            instance.export_figure_request.emit (file, settings, data);
        }

        public signal bool has_singularities_request (EquationItem item, double xstart, double xstop);
        public static bool has_singularities (EquationItem item, double xstart, double xstop) {
            return instance.has_singularities_request.emit (item, xstart, xstop);
        }

        protected signal void perform_operation_request (Window window, string name);
        public static void perform_operation (Window window, string name) {
            instance.perform_operation_request.emit (window, name);
        }

        protected signal void python_method_request (Object object, string method);
        public static void run_method (Object object, string method) {
            instance.python_method_request.emit (object, method);
        }

        protected signal string simplify_expression_request (Ast input);
        public static Ast simplify_expression (Ast input) throws MathError {
            string? simplified = instance.simplify_expression_request.emit (input);
            if (simplified == null) throw new MathError.DOMAIN ("unsupported expression");
            return expression_to_ast (simplified);
        }
    }

    public unowned string python_data_linestyle_to_style (DataLinestyle linestyle) {
        return linestyle.to_style ();
    }

    public unowned string python_data_markerstyle_to_style (DataMarkerstyle markerstyle) {
        return markerstyle.to_style ();
    }

    public unowned string python_data_plot_type_to_style (DataPlotType plottype) {
        return plottype.to_style ();
    }

    public unowned string python_data_step_position_to_style (DataStepPosition stepposition) {
        return stepposition.to_style ();
    }

    public unowned string python_equation_linestyle_to_style (EquationLinestyle linestyle) {
        return linestyle.to_style ();
    }
}
