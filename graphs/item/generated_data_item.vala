// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class GeneratedDataItem : DataItem, EquationBasedItem {
        public string xstart { get; set; default = "0"; }
        public string xstop { get; set; default = "10"; }
        public int steps { get; set; default = 100; }
        public Scale scale { get; set; default = Scale.LINEAR; }

        private Ast _equation;
        public Ast equation {
            get { return _equation; }
            set {
                try {
                    if (_equation != null && "Y = " + ast_to_expression (_equation) == name)
                        name = "Y = " + ast_to_expression (value);

                    _equation = value;
                } catch (MathError e) { assert_not_reached (); }

                regenerate ();
            }
        }

        construct {
            typename = _("Generated Dataset");

            const string[] PROPS = {"xstart", "xstop", "steps", "scale"};
            foreach (string prop in PROPS) {
                this.notify[prop].connect (regenerate);
            }
        }

        private void regenerate () {
            try {
                data = MathTools.equation_to_data (
                    _equation,
                    evaluate_string (xstart),
                    evaluate_string (xstop),
                    steps, scale);
            } catch (MathError e) { assert_not_reached (); }
        }
    }
}
