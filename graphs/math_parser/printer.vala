// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Printer {
        private StringBuilder builder;

        private static Once<Printer> _instance;

        public static unowned Printer instance () {
            return _instance.once (() => { return new Printer (); });
        }

        public string print (Ast ast) {
            this.builder = new StringBuilder ();
            emit (ast.root ());
            return builder.free_and_steal ();
        }

        private void emit (Expression expr) {
            switch (expr.type ()) {
                case ExpressionType.NUMBER: number (expr); return;
                case ExpressionType.CONSTANT: constant (expr); return;
                case ExpressionType.VARIABLE: variable (expr); return;
                case ExpressionType.UNARY: unary (expr); return;
                case ExpressionType.BINARY: binary (expr); return;
                case ExpressionType.POSTFIX: postfix (expr); return;
                case ExpressionType.FUNCTION: function (expr); return;
                default: assert_not_reached ();
            }
        }

        private const double PI_THRESH = 0.00010000314159265359; // 1e-4 + 1e-9 * pi
        private const double E_THRESH = 0.00010000271828182846; // 1e-4 + 1e-9 * e

        private void variable (Expression expr) {
            builder.append (expr.name ());
        }

        private void constant (Expression expr) {
            switch (expr.ident ()) {
                case Ident.PI: builder.append ("pi"); return;
                case Ident.E: builder.append_c ('e'); return;
                case Ident.INF: builder.append ("inf"); return;
                default: assert_not_reached ();
            }
        }

        private void number (Expression expr) {
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

        private void unary (Expression expr) {
            unowned Expression child = expr.right ();
            bool need_parens = child.type () == ExpressionType.BINARY;

            if (expr.op () == Operator.SUB) builder.append_c ('-');

            if (need_parens) builder.append_c ('(');
            emit (child);
            if (need_parens) builder.append_c (')');
        }

        private static inline unichar to_superscript (int i) {
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
                default: assert_not_reached ();
            }
        }

        private static bool need_parens (Expression expr, Expression parent, bool is_right_child) {
            if (!(expr.type () == ExpressionType.BINARY)) return false;
            if (!(parent.type () == ExpressionType.BINARY)) return true;

            int child_prec = expr.op ().precedence ();
            Operator parent_op = parent.op ();
            int parent_prec = parent_op.precedence ();

            if (child_prec != parent_prec) return child_prec < parent_prec;

            if (is_right_child)
                return parent_op == Operator.SUB || parent_op == Operator.DIV;
            return parent_op == Operator.POW;
        }

        private void binary (Expression expr) {
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
                    double exp = expr.right ().val ();
                    builder.append_unichar (to_superscript ((int) exp));
                    return;
                default: assert_not_reached ();
            }

            if (need_parens_right) builder.append_c ('(');
            emit (expr.right ());
            if (need_parens_right) builder.append_c (')');
        }

        private void postfix (Expression expr) {
            unowned Expression child = expr.left ();
            bool need_parens = child.type () == ExpressionType.BINARY;

            if (need_parens) builder.append_c ('(');
            emit (child);
            if (need_parens) builder.append_c (')');

            switch (expr.op ()) {
                case Operator.FACT: builder.append_c ('!'); break;
                default: assert_not_reached ();
            }
        }

        private void function (Expression expr) {
            Ident id = expr.ident ();

            EnumClass enumc = (EnumClass) typeof (Ident).class_ref ();
            unowned EnumValue? val = enumc.get_value (id);

            builder.append (val.value_nick);
            builder.append_c ('(');
            emit (expr.right ());
            builder.append_c (')');
        }
    }
}
