// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class FillHolder : Object {
        private double[] _xdata;
        private double[] _lower;
        private double[] _upper;

        public FillHolder (owned double[] xdata, owned double[] lower, owned double[] upper) {
            _xdata = (owned) xdata;
            _lower = (owned) lower;
            _upper = (owned) upper;
        }

        public FillHolder.empty () {
            _xdata = new double[0];
            _lower = new double[0];
            _upper = new double[0];
        }

        public unowned double[] get_xdata () {
            return _xdata;
        }

        public unowned double[] get_lower () {
            return _lower;
        }

        public unowned double[] get_upper () {
            return _upper;
        }

        public Bytes get_xdata_b () {
            return new Bytes ((uint8[]) _xdata);
        }

        public Bytes get_lower_b () {
            return new Bytes ((uint8[]) _lower);
        }

        public Bytes get_upper_b () {
            return new Bytes ((uint8[]) _upper);
        }
    }

    public enum FillBoundKind {
        DATA,
        ITEM,
        EQUATION
    }

    [Compact]
    private class FillBound {
        public FillBoundKind kind = FillBoundKind.DATA;
        public Item? item = null;
        public Ast? equation = null;
        public Program? program = null;
        public double constant = 0;
        public ulong handler = 0;
    }

    public enum FillBoundSelection {
        INF,
        NEG_INF,
        CUSTOM,
        TOP_ITEM
    }

    public class FillBounds : Object {
        public static Item[] get_source_items (Data data) {
            var items = new ManagedArray<Item> ((int) data.get_n_items ());
            foreach (Item item in data) {
                if (item is DataItem || item is EquationItem) items.append (item);
            }
            return items.steal ();
        }

        public static Gtk.StringList create_model (Item[] source_items) {
            var model = new Gtk.StringList (null);
            model.append (_("Positive Infinity"));
            model.append (_("Negative Infinity"));
            model.append (_("Custom Equation…"));
            assert (model.get_n_items () == FillBoundSelection.TOP_ITEM);
            foreach (Item item in source_items) {
                model.append (item.name);
            }
            return model;
        }

        public static string? get_expression (FillBoundSelection selected) {
            switch (selected) {
                case FillBoundSelection.INF: return "inf";
                case FillBoundSelection.NEG_INF: return "-inf";
                default: return null;
            }
        }

        public static uint get_selection (
            FillBoundKind kind, Item? source, Ast? equation,
            Item[] source_items
        ) {
            if (kind == FillBoundKind.ITEM) {
                if (source != null) {
                    for (uint i = 0; i < source_items.length; i++) {
                        if (source_items[i] == source) {
                            return (uint) FillBoundSelection.TOP_ITEM + i;
                        }
                    }
                }
                return FillBoundSelection.CUSTOM;
            }
            if (equation == null) return FillBoundSelection.CUSTOM;
            string expression;
            try {
                expression = ast_to_expression (equation);
            } catch (MathError e) { return FillBoundSelection.CUSTOM; }
            switch (expression) {
                case "inf": return FillBoundSelection.INF;
                case "-inf": return FillBoundSelection.NEG_INF;
                default: return FillBoundSelection.CUSTOM;
            }
        }
    }

    public class FillItem : Item, LegendableItem {
        public FillHolder data { get; set; default = new FillHolder.empty (); }

        public bool legend { get; set; default = false; }
        public signal void bounds_changed ();

        private FillBound _upper = new FillBound ();
        private FillBound _lower = new FillBound ();

        construct {
            typename = _("Fill");
            alpha = 0.4f;
        }

        public FillBoundKind get_upper_kind () {
            return _upper.kind;
        }

        public Item? get_upper_source () {
            return _upper.item;
        }

        public Ast? get_upper_equation () {
            return _upper.equation;
        }

        public unowned Program? get_upper_program () {
            return _upper.program;
        }

        public FillBoundKind get_lower_kind () {
            return _lower.kind;
        }

        public Item? get_lower_source () {
            return _lower.item;
        }

        public Ast? get_lower_equation () {
            return _lower.equation;
        }

        public unowned Program? get_lower_program () {
            return _lower.program;
        }

        public void set_upper_source (Item item) {
            set_source (_upper, item);
        }

        public void set_upper_equation (Ast equation) {
            set_equation (_upper, equation);
        }

        public void set_lower_source (Item item) {
            set_source (_lower, item);
        }

        public void set_lower_equation (Ast equation) {
            set_equation (_lower, equation);
        }

        private void set_source (FillBound bound, Item item) {
            detach_source (bound);
            bound.kind = FillBoundKind.ITEM;
            bound.item = item;
            bound.equation = null;
            bound.program = null;
            bound.handler = connect_source (item);
            item.register_dependent (this);
            if (this.color == "") this.color = item.color;
            recompute ();
        }

        private void set_equation (FillBound bound, Ast equation) {
            detach_source (bound);
            bound.kind = FillBoundKind.EQUATION;
            bound.equation = equation;
            bound.program = null;
            if (is_constant (equation.root ())) {
                try {
                    bound.constant = MathParser.Evaluator.instance ()
                        .eval_ast (equation);
                } catch (MathError e) {
                    /* A constant may still be undefined, e.g. 0/0. */
                    bound.constant = double.NAN;
                }
            } else {
                try {
                    bound.program = ast_to_program (equation, "x");
                } catch (MathError e) { assert_not_reached (); }
            }
            recompute ();
        }

        private ulong connect_source (Item item) {
            if (item is DataItem) {
                return item.notify["data"].connect (recompute);
            } else if (item is EquationItem) {
                return item.notify["equation"].connect (recompute);
            }
            return 0;
        }

        private static bool is_constant (Expression expression) {
            switch (expression.type ()) {
                case ExpressionType.VARIABLE:
                    return false;
                case ExpressionType.NUMBER:
                case ExpressionType.CONSTANT:
                    return true;
                case ExpressionType.UNARY:
                case ExpressionType.FUNCTION:
                    return is_constant (expression.right ());
                case ExpressionType.POSTFIX:
                    return is_constant (expression.left ());
                case ExpressionType.BINARY:
                    return is_constant (expression.left ())
                        && is_constant (expression.right ());
                default:
                    assert_not_reached ();
            }
        }

        private void detach_source (FillBound bound) {
            if (bound.item == null) return;
            Item item = bound.item;
            bound.item = null;
            if (bound.handler != 0) item.disconnect (bound.handler);
            bound.handler = 0;
            if (item != _upper.item && item != _lower.item) {
                item.unregister_dependent (this);
            }
        }

        public override void dispose () {
            detach_source (_upper);
            detach_source (_lower);
            base.dispose ();
        }

        private unowned double[]? get_target_x () {
            if (_upper.kind == FillBoundKind.ITEM && _upper.item is DataItem) {
                return ((DataItem) _upper.item).get_xdata ();
            }
            if (_lower.kind == FillBoundKind.ITEM && _lower.item is DataItem) {
                return ((DataItem) _lower.item).get_xdata ();
            }
            return null;
        }

        private double[] evaluate_bound (
            FillBound bound, double[] target
        ) throws MathError {
            if (bound.kind != FillBoundKind.ITEM) {
                if (bound.program != null) return bound.program.eval (target);
                double[] result = new double[target.length];
                CUtilities.fill_double (result, bound.constant);
                return result;
            }
            if (bound.item is DataItem) {
                var source = (DataItem) bound.item;
                return MathTools.interpolate (
                    source.get_xdata (), source.get_ydata (), target
                );
            }
            return ((EquationItem) bound.item).get_program ().eval (target);
        }

        public bool is_view_based () {
            return get_target_x () == null;
        }

        public void evaluate_bounds (
            double[] xdata, out double[] lower, out double[] upper
        ) throws MathError {
            lower = evaluate_bound (_lower, xdata);
            upper = evaluate_bound (_upper, xdata);
        }

        private void recompute () {
            unowned double[]? target = get_target_x ();
            if (target != null) {
                double[] x = new double[target.length];
                for (int i = 0; i < target.length; i++) x[i] = target[i];

                try {
                    double[] lower, upper;
                    evaluate_bounds (x, out lower, out upper);
                    data = new FillHolder (
                        (owned) x, (owned) lower, (owned) upper
                    );
                } catch (MathError e) {
                    warning ("Failed to evaluate fill bounds: %s", e.message);
                }
            }
            bounds_changed ();
        }
    }
}
