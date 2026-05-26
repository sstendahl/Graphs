// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Printer {
        private StringBuilder builder;
        private bool prettify;

        private static Once<Printer> _instance;

        public static unowned Printer instance () {
            return _instance.once (() => { return new Printer (); });
        }

        public string print (Expression ast, bool prettify = false) throws MathError {
            this.builder = new StringBuilder ();
            this.prettify = prettify;
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
            builder.append (expr.name ().down ());
        }

        private void constant (ConstantExpression expr) throws MathError {
            if (!prettify) {
                builder.append_printf ("%.15g", expr.val ());
                return;
            }

            switch (expr.constant ()) {
                case Ident.PI: builder.append ("pi"); return;
                case Ident.E: builder.append_c ('e'); return;
                case Ident.INF: builder.append ("inf"); return;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid constant");
            }
        }

        private void number (NumberExpression expr) throws MathError {
            double v = expr.val ();

            if (prettify) {
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
            }

            builder.append_printf ("%.15g", v);
        }

        private void unary (UnaryExpression expr) throws MathError {
            if (expr.op () == TokenType.MINUS) builder.append_c ('-');
            emit (expr.expr ());
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
                case TokenType.CARET:
                case TokenType.SUPERSCRIPT:
                    builder.append (prettify ? "^" : "**");
                    break;
                default: assert_not_reached ();
            }

            if (need_parens_right) builder.append_c ('(');
            emit (expr.right ());
            if (need_parens_right) builder.append_c (')');
        }

        private void postfix (PostfixExpression expr) throws MathError {
            emit (expr.expr ());

            switch (expr.op ()) {
                case TokenType.FACT:
                    builder.append_c ('!');
                    break;
                default: assert_not_reached ();
            }
        }

        private void function (FunctionExpression expr) throws MathError {
            Ident id = expr.ident ();

            if (prettify) {
                builder.append (id.to_string ()[13:].down ());
                builder.append_c ('(');
                emit (expr.arg ());
                builder.append_c (')');
                return;
            }

            function_pre (id);
            emit (expr.arg ());
            function_post (id);
        }

        private void function_pre (Ident id) {
            switch (id) {
                // trig radians
                case Ident.SIN: builder.append ("sin("); break;
                case Ident.COS: builder.append ("cos("); break;
                case Ident.TAN: builder.append ("tan("); break;
                case Ident.COT: builder.append ("1/tan("); break;
                case Ident.SEC: builder.append ("1/cos("); break;
                case Ident.CSC: builder.append ("1/sin("); break;

                // trig degrees
                case Ident.SIND: builder.append ("sin(0.017453292519943295*("); break;
                case Ident.COSD: builder.append ("cos(0.017453292519943295*("); break;
                case Ident.TAND: builder.append ("tan(0.017453292519943295*("); break;
                case Ident.COTD: builder.append ("1/tan(0.017453292519943295*("); break;
                case Ident.SECD: builder.append ("1/cos(0.017453292519943295*("); break;
                case Ident.CSCD: builder.append ("1/sin(0.017453292519943295*("); break;

                // inverse trig radians
                case Ident.ASIN: builder.append ("arcsin("); break;
                case Ident.ACOS: builder.append ("arccos("); break;
                case Ident.ATAN: builder.append ("arctan("); break;
                case Ident.ACOT: builder.append ("arcsin(1/sqrt(1+"); break;
                case Ident.ASEC: builder.append ("arccos(1/("); break;
                case Ident.ACSC: builder.append ("arcsin(1/("); break;

                // inverse trig degrees
                case Ident.ASIND: builder.append ("57.29577951308232*arcsin("); break;
                case Ident.ACOSD: builder.append ("57.29577951308232*arccos("); break;
                case Ident.ATAND: builder.append ("57.29577951308232*arctan("); break;
                case Ident.ACOTD: builder.append ("57.29577951308232*arcsin(1/sqrt(1+"); break;
                case Ident.ASECD: builder.append ("57.29577951308232*arccos(1/("); break;
                case Ident.ACSCD: builder.append ("57.29577951308232*arcsin(1/("); break;

                // misc
                case Ident.LOG: builder.append ("log("); break;
                case Ident.LOG2: builder.append ("log2("); break;
                case Ident.LOG10: builder.append ("log10("); break;
                case Ident.SQRT: builder.append ("sqrt("); break;
                case Ident.EXP: builder.append ("exp("); break;
                case Ident.ABS: builder.append ("abs("); break;

                default: assert_not_reached ();
            }
        }

        private void function_post (Ident id) {
            switch (id) {
                case Ident.ACOT: case Ident.ACOTD: builder.append ("**2))"); break;
                case Ident.SIND: case Ident.COSD: case Ident.TAND:
                case Ident.COTD: case Ident.SECD: case Ident.CSCD:
                case Ident.ASEC: case Ident.ACSC:
                case Ident.ASECD: case Ident.ACSCD:
                    builder.append ("))"); break;
                default: builder.append_c (')'); break;
            }
        }
    }
}
