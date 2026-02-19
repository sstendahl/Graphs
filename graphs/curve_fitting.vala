// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
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
        private unowned Box canvas_container { get; }

        [GtkChild]
        private unowned Box residuals_container { get; }

        [GtkChild]
        private unowned Adw.StatusPage error_page { get; }

        public Window window { get; construct set; }
        protected GLib.Settings settings { get; protected set; }
        protected string equation_string { get; protected set; }

        protected Canvas canvas {
            get { return canvas_container.get_first_child () as Canvas; }
            set {
                clear_container (canvas_container);
                if (value != null) {
                    canvas_container.append (value);
                    error_page.visible = false;
                } else {
                    error_page.visible = true;
                }
            }
        }

        protected Canvas residuals_canvas {
            get {
                return (Canvas) residuals_container.get_first_child ();
            }
            set {
                clear_container (residuals_container);
                if (canvas != null && value != null) {
                    residuals_container.append (value);
                    residuals_container.visible = settings.get_boolean ("show-residuals");
                } else {
                    residuals_container.visible = false;
                }
            }
        }

        protected signal bool equation_change (string[] free_vars);
        protected signal void fit_curve_request ();
        protected signal void add_fit_request ();
        protected signal void update_confidence_request ();
        public signal void show_residuals_changed (bool show);

        protected virtual void setup () {
            settings = Application.get_settings_child ("curve-fitting");
            var action_map = new SimpleActionGroup ();

            Action confidence_action = settings.create_action ("confidence");
            confidence_action.notify.connect (() => {
                update_confidence_request ();
            });
            action_map.add_action (confidence_action);

            Action optimization_action = settings.create_action ("optimization");
            optimization_action.notify.connect (() => {
                update_bounds_visibility ();
                fit_curve_request ();
            });
            action_map.add_action (optimization_action);

            Action res_action = settings.create_action ("show-residuals");
            res_action.notify.connect (() => {
                bool show_residuals = settings.get_boolean ("show-residuals");
                residuals_container.visible = (show_residuals && residuals_canvas != null);
                show_residuals_changed (show_residuals);
            });
            action_map.add_action (res_action);

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

            equation.set_selected (settings.get_enum ("equation"));
            equation.notify["selected"].connect (set_equation_from_selection);

            custom_equation.notify["text"].connect (on_custom_equation_text_changed);

            set_equation_from_selection ();
        }

        protected void set_results (CurveFittingError error) {
            var buffer = text_view.get_buffer ();
            buffer.set_text ("");
            var tag_table = buffer.get_tag_table ();
            var bold_tag = tag_table.lookup("bold");
            if (bold_tag == null) bold_tag = buffer.create_tag ("bold", "weight", 700);

            if (error != CurveFittingError.NONE) {
                TextIter end_iter;
                buffer.get_end_iter (out end_iter);
                buffer.insert (ref end_iter, error.to_text (), -1);
                confirm_button.set_sensitive (false);
                PythonHelper.run_method (this, "_clear_fit");
                return;
            }

            confirm_button.set_sensitive (true);
            PythonHelper.run_method (this, "_display_fit_results");
        }

        protected bool validate_and_update_parameter (FittingParameterBox row, FittingParameter param) {
            double init, low, high;
            bool value_error = false;

            var widget = row.initial;
            if (try_evaluate_string (widget.get_text (), out init)) {
                widget.remove_css_class ("error");
            } else {
                widget.add_css_class ("error");
            }

            widget = row.lower_bound;
            if (try_evaluate_string (widget.get_text (), out low)) {
                widget.remove_css_class ("error");
            } else {
                widget.add_css_class ("error");
            }

            widget = row.upper_bound;
            if (try_evaluate_string (widget.get_text (), out high)) {
                widget.remove_css_class ("error");
            } else {
                widget.add_css_class ("error");
            }

            if (value_error) {
                set_results (CurveFittingError.VALUE);
                return false;
            }

            if (low >= high) {
                row.lower_bound.add_css_class ("error");
                row.upper_bound.add_css_class ("error");
                set_results (CurveFittingError.BOUNDS);
                return false;
            }

            if (!(low <= init <= high)) {
                row.initial.add_css_class ("error");
                set_results (CurveFittingError.BOUNDS);
                return false;
            }

            param.initial = init;
            param.set_lower_bound (low);
            param.set_upper_bound (high);
            return true;
        }

        private void clear_container (Box container) {
            Widget? child = container.get_first_child ();
            while (child != null) {
                container.remove (child);
                child = container.get_first_child ();
            }
        }


        private void update_bounds_visibility () {
            bool visible = settings.get_string ("optimization") != "lm";
            var entry = (FittingParameterBox) fitting_params_box.get_first_child ();
            while (entry != null) {
                entry.set_bounds_visible (visible);
                entry = (FittingParameterBox) entry.get_next_sibling ();
            }
        }

        private void on_custom_equation_text_changed () {
            // Only validate if custom equation is visible
            if (equation.get_selected () != 7) return;

            string text = custom_equation.get_text ();
            if (handle_new_equation (text)) {
                custom_equation.remove_css_class ("error");
                settings.set_string ("custom-equation", text);
            } else {
                custom_equation.add_css_class ("error");
            }
        }

        private void set_equation_from_selection () {
            int selected = (int) equation.get_selected ();

            // Update settings if changed
            if (settings.get_enum ("equation") != selected) {
                settings.set_enum ("equation", selected);
            }

            string new_equation;
            if (selected != 7) {
                // Preset equation
                new_equation = EQUATIONS[selected];
                this.equation.set_subtitle (@"Y=$new_equation");
                custom_equation.set_visible (false);
            } else {
                // Custom equation
                new_equation = settings.get_string ("custom-equation");
                this.equation.set_subtitle ("");
                custom_equation.set_text (new_equation);
                custom_equation.set_visible (true);
            }

            handle_new_equation (new_equation);
        }

        private bool handle_new_equation (string equation) {
            try {
                string processed = preprocess_equation (equation);
                string[] free_vars = MathTools.get_free_variables (processed);

                if (free_vars.length == 0) {
                    set_results (CurveFittingError.EQUATION);
                    return false;
                }

                equation_string = processed;
                equation_change.emit (free_vars);
                fit_curve_request.emit ();
                return true;
            } catch (MathError e) {
                return false;
            }
        }

        [GtkCallback]
        private void emit_add_fit_request () {
            add_fit_request ();
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

        public FittingParameterBox (FittingParameter param) {
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
