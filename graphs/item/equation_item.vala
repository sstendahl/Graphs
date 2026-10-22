// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public enum EquationLinestyle {
        SOLID,
        DOTTED,
        DASHED,
        DASHDOT;

        public unowned string to_style () {
            EnumClass enumc = (EnumClass) typeof (EquationLinestyle).class_ref ();
            unowned EnumValue? eval = enumc.get_value (this);
            return eval.value_nick;
        }

        public static EquationLinestyle from_style (string style) {
            EnumClass enumc = (EnumClass) typeof (EquationLinestyle).class_ref ();
            unowned EnumValue? eval = enumc.get_value_by_nick (style);
            return (EquationLinestyle) eval.value;
        }
    }

    public class EquationItem : Item, EquationBasedItem, LegendableItem {
        public bool legend { get; set; default = true; }
        public EquationLinestyle linestyle { get; set; default = 1; }
        public double linewidth { get; set; default = 3; }

        private Ast _equation;
        private Program _program;
        public Ast equation {
            get { return _equation; }
            set {
                try {
                    if (_equation != null && "Y = " + ast_to_expression (_equation) == name)
                        name = "Y = " + ast_to_expression (value);

                    _equation = value;
                    _program = ast_to_program (value);
                } catch (MathError e) { assert_not_reached (); }
            }
        }

        construct {
            typename = _("Equation");
        }

        public unowned Program get_program () {
            return _program;
        }
    }
}
