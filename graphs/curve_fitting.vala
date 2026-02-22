// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gee;
using Gtk;

namespace Graphs {
    public class FittingParameter : Object {
        public string name { get; construct set; }
        public double initial { get; construct set; }
        // properties cannot assume infinite values
        private double lower_bound = -double.INFINITY;
        private double upper_bound = double.INFINITY;

        public FittingParameter (string name) {
            Object (name: name, initial: 1d);
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

    public class FitResult : Object {
        private double[] parameters;
        private double[] diag_covars;
        private double r2;
        private double rmse;

        public FitResult (double[] parameters, double[] diag_covars, double r2, double rmse) {
            this.parameters = parameters;
            this.diag_covars = diag_covars;
            this.r2 = r2;
            this.rmse = rmse;
        }

        public double[] get_parameters () {
            return parameters;
        }

        public double[] get_diag_covars () {
            return diag_covars;
        }

        public void get_r2_rmse (out double r2, out double rmse) {
            r2 = this.r2;
            rmse = this.rmse;
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

        public string to_text () {
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
    public class CurveFittingDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.ComboRow equation { get; }

        [GtkChild]
        protected unowned Button confirm_button { get; }

        [GtkChild]
        protected unowned Adw.EntryRow custom_equation { get; }

        [GtkChild]
        protected unowned Box fitting_params_box { get; }

        [GtkChild]
        protected unowned TextView text_view { get; }

        [GtkChild]
        private unowned Adw.ToastOverlay toast_overlay { get; }

        [GtkChild]
        private unowned Adw.OverlaySplitView split_view { get; }

        [GtkChild]
        private unowned Adw.Bin canvas_container { get; }

        [GtkChild]
        private unowned Adw.Bin residuals_container { get; }

        public Window window { get; construct set; }
        protected GLib.Settings settings { get; protected set; }
        protected string equation_string { get; private set; }
        protected string fitted_equation_string { get; protected set; }
        protected FitResult? fit_result { get; protected set; }

        private Map<string, FittingParameter> fitting_parameters;
        private string[] free_vars = {};

        protected Canvas? canvas {
            get { return canvas_container.get_child () as Canvas; }
            set { canvas_container.set_child (value); }
        }

        protected Canvas? residuals_canvas {
            get { return residuals_container.get_child () as Canvas; }
            set { residuals_container.set_child (value); }
        }

        protected virtual void setup () {
            fitting_parameters = new HashMap<string, FittingParameter> ();
            fit_result = null;

            settings = Application.get_settings_child ("curve-fitting");
            var action_map = new SimpleActionGroup ();

            Action confidence_action = settings.create_action ("confidence");
            confidence_action.notify.connect (() => {
                if (fit_result == null) return;
                PythonHelper.run_method (this, "_fit_curve");
            });
            action_map.add_action (confidence_action);

            Action optimization_action = settings.create_action ("optimization");
            optimization_action.notify.connect (() => {
                update_bounds_visibility ();
                PythonHelper.run_method (this, "_fit_curve");
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

            set_equation_from_selection ();
        }

        protected double[] get_p0 () {
            double[] result = new double[fitting_parameters.size];
            var iterator = fitting_parameters.map_iterator ();
            int idx = 0;
            while (iterator.has_next ()) {
                iterator.next ();
                result[idx++] = iterator.get_value ().initial;
            }
            return result;
        }

        protected void get_bounds (out double[] lower, out double[] upper) {
            lower = new double[fitting_parameters.size];
            upper = new double[fitting_parameters.size];
            var iterator = fitting_parameters.map_iterator ();
            int idx = 0;
            while (iterator.has_next ()) {
                iterator.next ();
                var param = iterator.get_value ();
                lower[idx] = param.get_lower_bound ();
                upper[idx] = param.get_upper_bound ();
                idx++;
            }
        }

        protected string[] get_free_vars () {
            return free_vars;
        }

        protected void set_results (CurveFittingError error) {
            var buffer = text_view.get_buffer ();
            buffer.set_text ("");
            var tag_table = buffer.get_tag_table ();
            var bold_tag = tag_table.lookup ("bold");
            if (bold_tag == null) bold_tag = buffer.create_tag ("bold", "weight", 700);

            TextIter end_iter;
            buffer.get_end_iter (out end_iter);

            if (error != CurveFittingError.NONE) {
                buffer.insert (ref end_iter, error.to_text (), -1);
                confirm_button.set_sensitive (false);
                fit_result = null;
                PythonHelper.run_method (this, "_clear_fit");
                return;
            }

            confirm_button.set_sensitive (true);
            if (fit_result == null) return;

            buffer.insert_with_tags_by_name (ref end_iter, _("Parameters") + "\n", -1, "bold");

            double[] diag_covars = fit_result.get_diag_covars ();
            double[] parameters = fit_result.get_parameters ();
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
            double r2, rmse;
            fit_result.get_r2_rmse (out r2, out rmse);
            string r2_rmse = "%s: %.3g\n%s: %.3g".printf (_("R²"), r2, _("RMSE"), rmse);
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
            param.initial = init;
            param.set_lower_bound (low);
            param.set_upper_bound (high);
            PythonHelper.run_method (this, "_fit_curve");
        }

        private void update_bounds_visibility () {
            bool visible =  settings.get_enum ("optimization") > 0;
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

            string new_equation;
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
            Widget widget;
            while ((widget = fitting_params_box.get_last_child ()) != null) {
                fitting_params_box.remove (widget);
            }

            try {
                equation_string = preprocess_equation (equation);
                free_vars = MathTools.get_free_variables (equation_string);

                if (free_vars.length == 0) {
                    set_results (CurveFittingError.EQUATION);
                    return false;
                }

                var new_map = new HashMap<string, FittingParameter> ();
                FittingParameter param;
                bool use_bounds = settings.get_enum ("optimization") > 0;
                foreach (string variable in free_vars) {
                    if (fitting_parameters.has_key (variable)) {
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

                PythonHelper.run_method (this, "_fit_curve");
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

            Item item = PythonHelper.add_equation (window, fitted_equation_string, "");
            Item[] items = {item};
            window.data.add_items (items);
            window.data.optimize_limits ();
            close ();
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/fitting-parameters.ui")]
    public class FittingParameterBox : Box {

        [GtkChild]
        private unowned Label label { get; }

        [GtkChild]
        public unowned Adw.EntryRow initial { get; }

        [GtkChild]
        public unowned Adw.EntryRow upper_bound { get; }

        [GtkChild]
        public unowned Adw.EntryRow lower_bound { get; }

        public FittingParameter param { get; construct set; }

        public FittingParameterBox (FittingParameter param) {
            this.param = param;
            string msg = _("Fitting Parameters for %s").printf (param.name);
            label.set_markup (@"<b> $msg: </b>");
            initial.set_text (param.initial.to_string ());
        }

        public void set_bounds_visible (bool visible) {
            upper_bound.set_visible (visible);
            lower_bound.set_visible (visible);
        }
    }
}
