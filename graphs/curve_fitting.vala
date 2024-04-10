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
        private unowned MenuButton menu_button { get; }

        public Application application { get; construct set; }
        protected GLib.Settings settings { get; private set; }
        protected string equation_string { get; protected set; }
        protected Canvas canvas {
            get { return (Canvas) this.toast_overlay.get_child (); }
            set { this.toast_overlay.set_child (value); }
        }

        protected signal bool equation_change (string equation);
        protected signal void fit_curve_request ();
        protected signal void add_fit_request ();

        protected void setup () {
            this.settings = this.application.get_settings_child ("curve-fitting");

            var action_map = new SimpleActionGroup ();
            Action confidence_action = this.settings.create_action ("confidence");
            Action optimization_action = this.settings.create_action ("optimization");
            confidence_action.notify.connect (emit_fit_curve_request);
            optimization_action.notify.connect (() => {
                emit_fit_curve_request ();
                bool visible = this.settings.get_string ("optimization") != "lm";
                var entry = (FittingParameterBox) this.fitting_params_box.get_first_child ();
                while (entry != null) {
                    entry.set_bounds_visible (visible);
                    entry = (FittingParameterBox) entry.get_next_sibling ();
                }
            });
            action_map.add_action (confidence_action);
            action_map.add_action (optimization_action);
            this.insert_action_group ("win", action_map);
            var confidence_section = new Menu ();
            string[] confidence_labels = {
                C_("confidence", "None"),
                C_("confidence", "1σ: 68% Confidence"),
                C_("confidence", "2σ: 95% Confidence"),
                C_("confidence", "3σ: 99.7% Confidence")
            };
            string[] confidence_targets = {"1std", "2std", "3std"};
            for (int i = 0; i < 4; i++) {
                string target = confidence_targets[i];
                confidence_section.append_item (new MenuItem (
                    confidence_labels[i], @"win.confidence::$target"
                ));
            }
            var menu = (Menu) this.menu_button.get_menu_model ();
            menu.append_section (_("Confidence Bounds"), confidence_section);

            this.equation.set_selected (this.settings.get_enum ("equation"));
            this.equation.notify["selected"].connect (set_equation);
            this.custom_equation.notify["text"].connect (() => {
                bool success = this.equation_change.emit (this.custom_equation.get_text ());
                if (success) this.custom_equation.remove_css_class ("error");
                else this.custom_equation.add_css_class ("error");
            });
            set_equation ();
        }

        private void emit_fit_curve_request () {
            this.fit_curve_request.emit ();
        }

        private void set_equation () {
            int selected = (int) this.equation.get_selected ();
            if (this.settings.get_enum ("equation") != selected ) {
                this.settings.set_enum ("equation", selected);
            }
            string equation;
            if (selected != 7) {
                equation = EQUATIONS[selected];
                this.equation.set_subtitle (@"Y=$equation");
                this.custom_equation.set_visible (false);
            } else {
                equation = this.settings.get_string ("custom-equation");
                this.equation.set_subtitle ("");
                this.settings.set_string ("custom-equation", equation);
                this.custom_equation.set_visible (true);
            }
            this.custom_equation.set_text (equation);
        }

        [GtkCallback]
        private void emit_add_fit_request () {
            this.add_fit_request.emit ();
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
            this.label.set_markup (@"<b> $msg: </b>");
            this.initial.set_text (param.initial.to_string ());
        }

        public void set_bounds_visible (bool visible) {
            this.upper_bound.set_visible (visible);
            this.lower_bound.set_visible (visible);
        }
    }
}
