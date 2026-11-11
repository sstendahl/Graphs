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
        private string[] _variables = {};
        private HashTable<string, double?> _values = new HashTable<string, double?> (str_hash, str_equal);

        public Ast equation {
            get { return _equation; }
            set {
                try {
                    if (_equation != null && "Y = " + ast_to_expression (_equation) == name)
                        name = "Y = " + ast_to_expression (value);

                    _equation = value;
                    _program = ast_to_parametric_program (value);
                    _variables = MathTools.get_free_variables (ast_to_expression (value));
                    foreach (unowned string variable in _program.get_parameters ()) {
                        _program.set_parameter (variable, get_variable_value (variable));
                    }
                } catch (MathError e) { assert_not_reached (); }
                values_changed.emit ();
            }
        }

        public signal void values_changed ();

        public signal void variable_changed (string name);

        construct {
            typename = _("Equation");
        }

        public EquationItem (StyleParameters parameters, Ast equation) {
            Object (
                equation: equation
            );
            override (parameters);
        }

        private static StylePropertyBinding[] bindings = {
            {"linestyle", (s) => s.linestyle - 1},
            {"linewidth", (s) => s.linewidth}
        };

        protected override unowned StylePropertyBinding[]? get_property_bindings () {
            return bindings;
        }

        public unowned Program get_program () {
            return _program;
        }

        public string[] get_variables () {
            return _variables;
        }

        public bool has_variable (string name) {
            return name in _variables;
        }

        public double get_variable_value (string name) {
            double? val = _values.lookup (name);
            return val == null ? 1 : val;
        }

        public void set_variable_value (string name, double val) {
            if (_values.contains (name) && get_variable_value (name) == val) return;
            _values.insert (name, val);
            if (!has_variable (name)) return;

            _program.set_parameter (name, val);
            variable_changed.emit (name);
            values_changed.emit ();
        }

        /**
         * Get the equation with the variables replaced by their values, giving a
         * normal equation without free variables to evaluate
         */
        public Ast get_bound_equation () {
            Ast result = _equation;
            foreach (unowned string variable in _variables) {
                result = ast_bind_variable (result, variable, get_variable_value (variable));
            }
            return result;
        }
    }
}
