// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    public class FittingParameter : Object {
        public string name { get; construct set; }
        public double initial { get; construct set; }
        public string lower_bound { get; construct set; }
        public string upper_bound { get; construct set; }
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

        private Canvas? _main_canvas = null;
        private Canvas? _residuals_canvas = null;

        protected Canvas canvas {
            get { return _main_canvas; }
            set {
                clear_container (canvas_container);
                _main_canvas = value;
                if (_main_canvas != null) {
                    canvas_container.append (_main_canvas);
                    error_page.visible = false;
                } else {
                    error_page.visible = true;
                }
            }
        }

        protected Canvas residuals_canvas {
            get { return _residuals_canvas; }
            set {
                clear_container (residuals_container);
                _residuals_canvas = value;
                if (_residuals_canvas != null) {
                    residuals_container.append (_residuals_canvas);
                    residuals_container.visible = settings.get_boolean ("show-residuals");
                } else {
                    residuals_container.visible = false;
                }
            }
        }

        private void clear_container (Box container) {
            Widget? child = container.get_first_child ();
            while (child != null) {
                container.remove (child);
                child = container.get_first_child ();
            }
        }

        protected signal bool equation_change (string equation);
        protected signal void fit_curve_request ();
        protected signal void add_fit_request ();
        public signal void show_residuals_changed (bool show);

        protected virtual void setup () {
            var application = window.application as Application;
            settings = application.get_settings_child ("curve-fitting");
            var action_map = new SimpleActionGroup ();
            Action confidence_action = settings.create_action ("confidence");
            confidence_action.notify.connect (emit_fit_curve_request);
            action_map.add_action (confidence_action);

            Action optimization_action = settings.create_action ("optimization");
            optimization_action.notify.connect (() => {
                emit_fit_curve_request ();
                bool visible = settings.get_string ("optimization") != "lm";
                var entry = fitting_params_box.get_first_child () as FittingParameterBox;
                while (entry != null) {
                    entry.set_bounds_visible (visible);
                    entry = entry.get_next_sibling () as FittingParameterBox;
                }
            });
            action_map.add_action (optimization_action);

            Action res_action = settings.create_action ("show-residuals");
            res_action.notify.connect (() => {
                bool show_residuals = settings.get_boolean ("show-residuals");
                residuals_container.visible = (show_residuals && _residuals_canvas != null);
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
            equation.notify["selected"].connect (set_equation);
            custom_equation.notify["text"].connect (() => {
                bool success = equation_change.emit (custom_equation.get_text ());
                if (success) {
                    custom_equation.remove_css_class ("error");
                } else custom_equation.add_css_class ("error");
            });

            custom_equation.apply.connect (() => {
                if (equation.get_selected () == 7) {
                    settings.set_string ("custom-equation", custom_equation.get_text ());
                    emit_fit_curve_request ();
                }
            });
            set_equation ();
        }

        private void emit_fit_curve_request () {
            fit_curve_request.emit ();
        }

        private void set_equation () {
            int selected = (int) equation.get_selected ();
            if (settings.get_enum ("equation") != selected ) {
                settings.set_enum ("equation", selected);
            }
            string equation;
            if (selected != 7) {
                equation = EQUATIONS[selected];
                this.equation.set_subtitle (@"Y=$equation");
                custom_equation.set_visible (false);
            } else {
                equation = settings.get_string ("custom-equation");
                this.equation.set_subtitle ("");
                settings.set_string ("custom-equation", equation);
                custom_equation.set_visible (true);
            }
            custom_equation.set_text (equation);
            emit_fit_curve_request ();
        }

        [GtkCallback]
        private void emit_add_fit_request () {
            add_fit_request.emit ();
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
