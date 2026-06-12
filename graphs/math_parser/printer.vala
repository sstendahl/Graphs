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
            if (expr.op () == TokenType.MINUS) builder.append_c ('-');
            emit (expr.expr ());
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

        private void binary (BinaryExpression expr) throws MathError {
            bool need_parens_left = expr.left () is BinaryExpression;
            bool need_parens_right = expr.right () is BinaryExpression;

            if (need_parens_left) builder.append_c ('(');
            emit (expr.left ());
            if (need_parens_left) builder.append_c (')');

            switch (expr.op ()) {
                case TokenType.PLUS: builder.append (" + "); break;
                case TokenType.MINUS: builder.append (" - "); break;
                case TokenType.STAR: builder.append (" * "); break;
                case TokenType.SLASH: builder.append (" / "); break;
                case TokenType.CARET: builder.append_c ('^'); break;
                case TokenType.SUPERSCRIPT:
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
            emit (expr.expr ());

            switch (expr.op ()) {
                case TokenType.FACT: builder.append_c ('!'); break;
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
