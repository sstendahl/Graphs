// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Printer {
        private StringBuilder builder;

        private static Once<Printer> _instance;

        public static unowned Printer instance () {
            return _instance.once (() => { return new Printer (); });
        }

        public string print (Expression ast) throws MathError {
            this.builder = new StringBuilder ();
            emit (ast);
            return builder.free_and_steal ();
        }

        private void emit (Expression expr) throws MathError {
            if (expr is NumberExpression) { number ((NumberExpression) expr); return; }
            if (expr is ConstantExpression) { constant ((ConstantExpression) expr); return; }
            if (expr is VariableExpression) { variable ((VariableExpression) expr); return; }
            if (expr is UnaryExpression) { unary ((UnaryExpression) expr); return; }
            if (expr is BinaryExpression) { binary ((BinaryExpression) expr); return; }
            if (expr is FunctionExpression) { function ((FunctionExpression) expr); return; }
            if (expr is PostfixExpression) { postfix ((PostfixExpression) expr); return; }

            assert_not_reached ();
        }

        private const double PI_THRESH = 0.00010000314159265359; // 1e-4 + 1e-9 * pi
        private const double E_THRESH = 0.00010000271828182846; // 1e-4 + 1e-9 * e

        private void variable (VariableExpression expr) throws MathError {
            builder.append (expr.name ());
        }

        private void constant (ConstantExpression expr) throws MathError {
            switch (expr.constant ()) {
                case Ident.PI: builder.append ("pi"); return;
                case Ident.E: builder.append_c ('e'); return;
                case Ident.INF: builder.append ("inf"); return;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid constant");
            }
        }

        private void number (NumberExpression expr) throws MathError {
            double v = expr.val ();

            // check if it is a multiple of pi
            double remainder = Math.fmod (v, Math.PI);
            if (remainder <= PI_THRESH || remainder >= Math.PI - PI_THRESH) {
                // fast rounding check evasion
                double factor = Math.floor (v / Math.PI + 0.5);
                if (factor != 0) {
                    if (factor != 1) builder.append ("%.15g".printf (factor));
                    builder.append ("pi");
                    return;
                }
            }

            // or e
            remainder = Math.fmod (v, Math.E);
            if (remainder <= E_THRESH || remainder >= Math.E - E_THRESH) {
                // fast rounding check evasion
                double factor = Math.floor (v / Math.E + 0.5);
                if (factor != 0) {
                    if (factor != 1) builder.append ("%.15g".printf (factor));
                    builder.append_c ('e');
                    return;
                }
            }

            builder.append_printf ("%.15g", v);
        }

        private void unary (UnaryExpression expr) throws MathError {
            bool need_parens = expr.expr () is BinaryExpression;

            if (expr.op () == Operator.SUB) builder.append_c ('-');

            if (need_parens) builder.append_c ('(');
            emit (expr.expr ());
            if (need_parens) builder.append_c (')');
        }

        private static inline unichar to_superscript (int i) throws MathError {
            switch (i) {
                case 0: return '⁰';
                case 1: return '¹';
                case 2: return '²';
                case 3: return '³';
                case 4: return '⁴';
                case 5: return '⁵';
                case 6: return '⁶';
                case 7: return '⁷';
                case 8: return '⁸';
                case 9: return '⁹';
                default: throw new MathError.SYNTAX ("invalid superscript");
            }
        }

        private static bool need_parens (Expression expr, Expression parent, bool is_right_child) {
            if (!(expr is BinaryExpression)) return false;
            if (!(parent is BinaryExpression)) return true;

            int child_prec = ((BinaryExpression) expr).op ().precedence ();
            Operator parent_op = ((BinaryExpression) parent).op ();
            int parent_prec = parent_op.precedence ();

            if (child_prec != parent_prec) return child_prec < parent_prec;

            if (is_right_child)
                return parent_op == Operator.SUB || parent_op == Operator.DIV;
            return parent_op == Operator.POW;
        }

        private void binary (BinaryExpression expr) throws MathError {
            bool need_parens_left = need_parens (expr.left (), expr, false);
            bool need_parens_right = need_parens (expr.right (), expr, true);

            if (need_parens_left) builder.append_c ('(');
            emit (expr.left ());
            if (need_parens_left) builder.append_c (')');

            switch (expr.op ()) {
                case Operator.ADD: builder.append (" + "); break;
                case Operator.SUB: builder.append (" - "); break;
                case Operator.DIV: builder.append (" / "); break;
                case Operator.POW: builder.append_c ('^'); break;
                case Operator.MUL:
                    builder.append (need_parens_left && need_parens_right ? " " : " * ");
                    break;
                case Operator.SUPERSCRIPT:
                    double exp = ((NumberExpression) expr.right ()).val ();
                    builder.append_unichar (to_superscript ((int) exp));
                    return;
                default: throw new MathError.SYNTAX ("invalid binary expression");
            }

            if (need_parens_right) builder.append_c ('(');
            emit (expr.right ());
            if (need_parens_right) builder.append_c (')');
        }

        private void postfix (PostfixExpression expr) throws MathError {
            bool need_parens = expr.expr () is BinaryExpression;

            if (need_parens) builder.append_c ('(');
            emit (expr.expr ());
            if (need_parens) builder.append_c (')');

            switch (expr.op ()) {
                case Operator.FACT: builder.append_c ('!'); break;
                default: throw new MathError.SYNTAX ("invalid postfix expression");
            }
        }

        private void function (FunctionExpression expr) throws MathError {
            Ident id = expr.ident ();

            EnumClass enumc = (EnumClass) typeof (Ident).class_ref ();
            unowned EnumValue? val = enumc.get_value (id);

            builder.append (val.value_nick);
            builder.append_c ('(');
            emit (expr.arg ());
            builder.append_c (')');
        }
    }
}
