// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class FittingParameter {
        private string name;
        private double initial = 1d;
        private double lower_bound = -double.INFINITY;
        private double upper_bound = double.INFINITY;

        public FittingParameter (owned string name) {
            this.name = (owned) name;
        }

        public unowned string get_name () {
            return name;
        }

        public double get_initial () {
            return initial;
        }

        public void set_initial (double initial) {
            this.initial = initial;
        }

        public double get_lower_bound () {
            return lower_bound;
        }

        public void set_lower_bound (double lower_bound) {
            this.lower_bound = lower_bound;
        }

        public double get_upper_bound () {
            return upper_bound;
        }

        public void set_upper_bound (double upper_bound) {
            this.upper_bound = upper_bound;
        }
    }

    public class FitProblem {
        public DataHolder data;
        public string[] free_vars;
        public Ast expression;
        public Settings settings;
        public FittingParameter[] parameters;
        public Bytes x_fit;
    }

    public class FitResult {
        public double[] parameters;
        public double[] diag_covars;
        public double r2;
        public double rmse;
        public DataHolder residuals;
        public string fitted_equation_string;
        public DataHolder fit;
        public FillHolder confidence;

        // Python cannot mutate specific field types
        public void set_parameters (owned double[] parameters) {
            this.parameters = (owned) parameters;
        }

        public void set_diag_covars (owned double[] diag_covars) {
            this.diag_covars = (owned) diag_covars;
        }
    }

    public enum CurveFittingError {
        NONE,
        VALUE,
        BOUNDS,
        SINGULAR,
        CONVERGENCE,
        DOMAIN,
        EQUATION,
        CONFIDENCE;

        public unowned string to_text () {
            switch (this) {
                case VALUE: return _("Please enter valid \nnumeric parameters.");
                case BOUNDS: return _("Constraint error: ensure \nLower < Initial < Upper.");
                case SINGULAR: return _("Matrix error: Data is \ninsufficient for this model.");
                case CONVERGENCE: return _("Fit failed: Max iterations \nreached without converging.");
                case DOMAIN: return _("Domain error: Equation not \nvalid for this data range.");
                case EQUATION: return _("Invalid equation: Check \nsyntax and variables.");
                case CONFIDENCE: return _("Confidence band error: \nCovariance matrix is unstable.");
                default: assert_not_reached ();
            }
        }
    }

    private const string[] EQUATIONS = {
        "a*x+b", // linear
        "a*x²+b*x+c", // quadratic
        "a*exp(b*x)", // exponential
        "a*x^b", // power
        "a*log(x)+b", // log
        "L/(1+exp(-k*(x-b)))", // sigmoid
        "a*exp(-(x-mu)²/(2*s²))" // gaussian
    };

    /**
     * Curve fitting dialog.
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/curve-fitting.ui")]
    private class CurveFittingDialog : Adw.Dialog {
        private const string DATA_COLOR = "#1A5FB4";
        private const string FIT_COLOR = "#A51D2D";
        private const string FILL_COLOR = "#62A0EA";
        private const float FILL_ALPHA = 0.25f;

        [GtkChild]
        private unowned Adw.ComboRow equation { get; }

        [GtkChild]
        private unowned Gtk.Button confirm_button { get; }

        [GtkChild]
        private unowned Adw.EntryRow custom_equation { get; }

        [GtkChild]
        private unowned Gtk.Box fitting_params_box { get; }

        [GtkChild]
        private unowned Gtk.TextView text_view { get; }

        [GtkChild]
        private unowned Adw.ToastOverlay toast_overlay { get; }

        [GtkChild]
        private unowned Adw.OverlaySplitView split_view { get; }

        [GtkChild]
        private unowned Adw.Bin canvas_container { get; }

        [GtkChild]
        private unowned Adw.Bin residuals_container { get; }

        private Window window;
        private Settings settings;
        private Ast ast;
        private Bytes x_fit;
        private HashTable<string, FittingParameter> fitting_parameters;
        private string[] free_vars = {};
        private FigureSettings canvas_settings;
        private FigureSettings residuals_settings;
        private DataHolder data;
        private FitResult? fit_result;
        private ListStore main_canvas_items;
        private ListStore residuals_canvas_items;

        private Canvas? canvas {
            get { return canvas_container.get_child () as Canvas; }
            set { canvas_container.set_child (value); }
        }

        private Canvas? residuals_canvas {
            get { return residuals_container.get_child () as Canvas; }
            set { residuals_container.set_child (value); }
        }

        construct {
            fitting_parameters = new HashTable<string, FittingParameter> (str_hash, str_equal);
            fit_result = null;

            settings = Application.get_settings_child ("curve-fitting");
            var action_map = new SimpleActionGroup ();

            Action confidence_action = settings.create_action ("confidence");
            confidence_action.notify.connect (() => {
                if (fit_result == null) return;
                fit_curve ();
            });
            action_map.add_action (confidence_action);

            Action optimization_action = settings.create_action ("optimization");
            optimization_action.notify.connect (() => {
                update_bounds_visibility ();
                fit_curve ();
            });
            action_map.add_action (optimization_action);

            Action res_action = settings.create_action ("show-residuals");
            res_action.notify.connect (() => {
                bool show_residuals = settings.get_boolean ("show-residuals");
                residuals_container.set_visible (show_residuals && residuals_canvas != null);
            });
            action_map.add_action (res_action);
            bool show_residuals = settings.get_boolean ("show-residuals");
            residuals_container.set_visible (show_residuals && residuals_canvas != null);

            var toggle_sidebar_action = new SimpleAction ("toggle_sidebar", null);
            toggle_sidebar_action.activate.connect (() => {
                split_view.show_sidebar = !split_view.show_sidebar;
            });
            split_view.bind_property (
                "collapsed",
                toggle_sidebar_action,
                "enabled",
                BindingFlags.SYNC_CREATE
            );
            action_map.add_action (toggle_sidebar_action);
            insert_action_group ("win", action_map);

            custom_equation.set_text (settings.get_string ("custom-equation"));
            equation.set_selected (settings.get_enum ("equation"));
            equation.notify["selected"].connect (set_equation_from_selection);

            custom_equation.notify["text"].connect (on_custom_equation_text_changed);
        }

        private StyleParameters get_canvas_style () {
            var data = window.data;
            if (!data.figure_settings.use_custom_style) return StyleManager.get_system_style_params ();
            return StyleManager.get_system_style_params_for (data.selected_style_params);
        }

        public CurveFittingDialog (Window window, DataItem item) {
            this.window = window;
            this.data = item.data;

            var style = get_canvas_style ();

            double x_min, x_max;
            CUtilities.array_minmax (item.get_xdata (), false, out x_min, out x_max);
            double padding = (x_max - x_min) * 0.025;
            x_min -= padding;
            x_max += padding;

            var xdata = new double[5000];
            CUtilities.create_equidistant_data (x_min, x_max, Scale.LINEAR, xdata);
            x_fit = new Bytes ((uint8[]) xdata);

            var data_curve = new DataItem (style, item.get_xdata (), item.get_ydata ());
            data_curve.name = item.name;
            data_curve.color = DATA_COLOR;
            data_curve.markersize = 13;
            data_curve.markerstyle = POINT;
            data_curve.linestyle = SOLID;

            var fitted_curve = new DataItem (style, {}, {});
            fitted_curve.color = FIT_COLOR;

            var fill = new FillItem (style, {}, {}, {});
            fill.color = FILL_COLOR;
            fill.alpha = FILL_ALPHA;

            var residuals = new DataItem (style, {}, {});
            residuals.color = DATA_COLOR;
            residuals.markersize = 13;
            residuals.markerstyle = POINT;
            residuals.linestyle = SOLID;

            var marker = new MarkerItem (style, HORIZONTAL, 0);
            marker.linewidth = 0.5;
            marker.linestyle = DASHED;

            main_canvas_items = new ListStore (typeof (Item));
            main_canvas_items.append (fitted_curve);
            main_canvas_items.append (fill);
            main_canvas_items.append (data_curve);

            residuals_canvas_items = new ListStore (typeof (Item));
            residuals_canvas_items.append (residuals);
            residuals_canvas_items.append (marker);

            var figure_settings = window.data.figure_settings;

            canvas_settings = new FigureSettings.default ();
            canvas_settings.bottom_label = figure_settings.bottom_label;
            canvas_settings.left_label = figure_settings.left_label;
            canvas_settings.min_bottom = x_min;
            canvas_settings.max_bottom = x_max;

            residuals_settings = new FigureSettings.default ();
            residuals_settings.bottom_label = figure_settings.bottom_label;
            residuals_settings.left_label = _("Residuals");
            residuals_settings.min_left = -1;
            residuals_settings.max_left = 1;
            residuals_settings.min_bottom = x_min;
            residuals_settings.max_bottom = x_max;
            residuals_settings.legend = false;

            load_canvas ();
            Adw.StyleManager.get_default ().notify.connect (load_canvas);
            set_equation_from_selection ();

            present (window);
        }

        private void load_canvas () {
            var style = get_canvas_style ();
            canvas = PythonHelper.create_canvas (style, main_canvas_items, false, canvas_settings);
            residuals_canvas = PythonHelper.create_canvas (style, residuals_canvas_items, false, residuals_settings);
            residuals_container.set_visible (settings.get_boolean ("show-residuals"));
        }

        private void fit_curve () {
            var problem = new FitProblem ();
            problem.data = data;
            problem.free_vars = free_vars;
            problem.expression = ast;
            problem.settings = settings;
            problem.x_fit = x_fit;

            FittingParameter[] parameters = new FittingParameter[free_vars.length];
            for (int i = 0; i < free_vars.length; i++) {
                parameters[i] = fitting_parameters.get (free_vars[i]);
            }
            problem.parameters = parameters;

            fit_result = new FitResult ();
            set_results (PythonHelper.curve_fit (problem, fit_result));
        }

        private void set_results (CurveFittingError error) {
            var buffer = text_view.get_buffer ();
            buffer.set_text ("");
            var tag_table = buffer.get_tag_table ();
            var bold_tag = tag_table.lookup ("bold");
            if (bold_tag == null) bold_tag = buffer.create_tag ("bold", "weight", 700);

            Gtk.TextIter end_iter;
            buffer.get_end_iter (out end_iter);

            var fitted_curve = (DataItem) main_canvas_items.get_item (0);
            var fill = (FillItem) main_canvas_items.get_item (1);
            var data_curve = (DataItem) main_canvas_items.get_item (2);
            var residuals = (DataItem) residuals_canvas_items.get_item (0);

            if (error != CurveFittingError.NONE) {
                buffer.insert (ref end_iter, error.to_text (), -1);
                confirm_button.set_sensitive (false);
                fit_result = null;

                fitted_curve.visible = false;
                fill.visible = false;
                residuals.visible = false;
                residuals_settings.min_left = -1;
                residuals_settings.max_left = 1;

                return;
            }

            fitted_curve.visible = true;
            fill.visible = true;
            residuals.visible = true;

            confirm_button.set_sensitive (true);
            if (fit_result == null) return;

            residuals.data = fit_result.residuals;
            fitted_curve.data = fit_result.fit;
            fitted_curve.name = "Y = " + fit_result.fitted_equation_string;
            fill.data = fit_result.confidence;

            double min_y, max_y;
            double tmp_min_y, tmp_max_y;

            CUtilities.array_minmax (fill.data.get_lower (), false, out min_y, out max_y);
            CUtilities.array_minmax (fill.data.get_upper (), false, out tmp_min_y, out tmp_max_y);
            min_y = double.min (min_y, tmp_min_y);
            max_y = double.max (max_y, tmp_max_y);
            CUtilities.array_minmax (data_curve.get_ydata (), false, out tmp_min_y, out tmp_max_y);
            min_y = double.min (min_y, tmp_min_y);
            max_y = double.max (max_y, tmp_max_y);
            double padding = (max_y - min_y) * 0.025;
            canvas_settings.min_left = min_y - padding;
            canvas_settings.max_left = max_y + padding;

            CUtilities.array_minmax (residuals.get_ydata (), false, out min_y, out max_y);
            double max_residual = double.max (Math.fabs (min_y), Math.fabs (max_y));
            if (max_residual > 0)
                max_residual *= 1.1;
            else
                max_residual = 1;
            residuals_settings.min_left = -max_residual;
            residuals_settings.max_left = max_residual;

            buffer.insert_with_tags_by_name (ref end_iter, _("Parameters") + "\n", -1, "bold");

            unowned double[] diag_covars = fit_result.diag_covars;
            unowned double[] parameters = fit_result.parameters;
            int conf_level = settings.get_enum ("confidence");

            int n = free_vars.length;
            for (int i = 0; i < n; i++) {
                buffer.insert (ref end_iter, "%s: %.3g".printf (free_vars[i], parameters[i]), -1);
                if (conf_level > 0) {
                    double err = diag_covars[i] * conf_level;
                    buffer.insert (ref end_iter, " (± %.3g)".printf (err), -1);
                }
                buffer.insert (ref end_iter, "\n", -1);
            }

            buffer.insert_with_tags_by_name (ref end_iter, "\n" + _("Statistics") + "\n", -1, "bold");
            string r2_rmse = "%s: %.3g\n%s: %.3g".printf (_("R²"), fit_result.r2, _("RMSE"), fit_result.rmse);
            buffer.insert (ref end_iter, r2_rmse, -1);
        }

        private void on_entry_change (Object object, ParamSpec p) {
            var entry = (Adw.EntryRow) object;
            var row = (FittingParameterBox) entry.get_ancestor (typeof (FittingParameterBox));

            double init, low, high;
            bool value_error = false;

            var widget = row.initial;
            if (try_evaluate_string (widget.get_text (), out init)) {
                widget.remove_css_class ("error");
            } else {
                widget.add_css_class ("error");
                value_error = true;
            }

            widget = row.lower_bound;
            if (try_evaluate_string (widget.get_text (), out low)) {
                widget.remove_css_class ("error");
            } else {
                widget.add_css_class ("error");
                value_error = true;
            }

            widget = row.upper_bound;
            if (try_evaluate_string (widget.get_text (), out high)) {
                widget.remove_css_class ("error");
            } else {
                widget.add_css_class ("error");
                value_error = true;
            }

            if (value_error) {
                set_results (CurveFittingError.VALUE);
                return;
            }

            if (low >= high) {
                row.lower_bound.add_css_class ("error");
                row.upper_bound.add_css_class ("error");
                set_results (CurveFittingError.BOUNDS);
                return;
            }

            if (!(low <= init <= high)) {
                row.initial.add_css_class ("error");
                set_results (CurveFittingError.BOUNDS);
                return;
            }

            var param = row.param;
            param.set_initial (init);
            param.set_lower_bound (low);
            param.set_upper_bound (high);
            fit_curve ();
        }

        private void update_bounds_visibility () {
            bool visible = settings.get_enum ("optimization") > 0;
            var entry = (FittingParameterBox) fitting_params_box.get_first_child ();
            while (entry != null) {
                entry.set_bounds_visible (visible);
                entry = (FittingParameterBox) entry.get_next_sibling ();
            }
        }

        private void on_custom_equation_text_changed () {
            // Only validate if custom equation is visible
            if (equation.get_selected () != 7) return;

            if (handle_new_equation (custom_equation.get_text ())) {
                custom_equation.remove_css_class ("error");
            } else {
                custom_equation.add_css_class ("error");
            }
        }

        private void set_equation_from_selection () {
            int selected = (int) equation.get_selected ();

            unowned string new_equation;
            if (selected != 7) {
                // Preset equation
                new_equation = EQUATIONS[selected];
                this.equation.set_subtitle (@"Y=$new_equation");
                custom_equation.set_visible (false);
            } else {
                // Custom equation
                new_equation = custom_equation.get_text ();
                this.equation.set_subtitle ("");
                custom_equation.set_visible (true);
            }

            handle_new_equation (new_equation);
        }

        private bool handle_new_equation (string equation) {
            // clear existing widgets
            Gtk.Widget widget;
            while ((widget = fitting_params_box.get_last_child ()) != null) {
                fitting_params_box.remove (widget);
            }

            try {
                ast = expression_to_ast (equation);
                free_vars = MathTools.get_free_variables (equation);

                if (free_vars.length == 0) {
                    set_results (CurveFittingError.EQUATION);
                    return false;
                }

                var new_map = new HashTable<string, FittingParameter> (str_hash, str_equal);
                FittingParameter param;
                bool use_bounds = settings.get_enum ("optimization") > 0;
                foreach (unowned string variable in free_vars) {
                    if (fitting_parameters.contains (variable)) {
                        param = fitting_parameters.get (variable);
                    } else {
                        param = new FittingParameter (variable);
                    }

                    var p_box = new FittingParameterBox (param);
                    p_box.set_bounds_visible (use_bounds);

                    p_box.initial.notify["text"].connect (on_entry_change);
                    p_box.upper_bound.notify["text"].connect (on_entry_change);
                    p_box.lower_bound.notify["text"].connect (on_entry_change);

                    fitting_params_box.append (p_box);
                    new_map.set (variable, param);
                }
                fitting_parameters = new_map;

                fit_curve ();
                return true;
            } catch (MathError e) {
                set_results (CurveFittingError.EQUATION);
                return false;
            }
        }

        [GtkCallback]
        private void on_accept () {
            settings.set_enum ("equation", (int) equation.get_selected ());
            settings.set_string ("custom-equation", custom_equation.get_text ());

            try {
                Ast ast = expression_to_ast (fit_result.fitted_equation_string);
                Item item = new EquationItem (window.data.selected_style_params, ast) {
                    name = "Y = " + fit_result.fitted_equation_string,
                };
                Item[] items = {item};
                window.data.add_items (items);
            } catch (MathError e) { assert_not_reached (); }

            window.data.optimize_limits ();
            close ();
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/fitting-parameters.ui")]
    private class FittingParameterBox : Gtk.Box {

        [GtkChild]
        private unowned Gtk.Label label { get; }

        [GtkChild]
        public unowned Adw.EntryRow initial { get; }

        [GtkChild]
        public unowned Adw.EntryRow upper_bound { get; }

        [GtkChild]
        public unowned Adw.EntryRow lower_bound { get; }

        public FittingParameter param { get; construct set; }

        public FittingParameterBox (FittingParameter param) {
            this.param = param;
            string msg = _("Fitting Parameters for %s").printf (param.get_name ());
            label.set_markup (@"<b> $msg: </b>");
            initial.set_text (param.get_initial ().to_string ());
        }

        public void set_bounds_visible (bool visible) {
            upper_bound.set_visible (visible);
            lower_bound.set_visible (visible);
        }
    }
}
