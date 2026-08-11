// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    [Compact]
    private class Evaluator {
        private static Once<Evaluator> _instance;

        public static unowned Evaluator instance () {
            return _instance.once (() => { return new Evaluator (); });
        }

        public double eval_ast (Ast expr) throws MathError {
            double result = eval (expr.root ());

            if (result.is_nan ())
                throw new MathError.INVALID ("expression is not a number");

            return result;
        }

        private double eval (Expression expr) {
            switch (expr.type ()) {
                case ExpressionType.NUMBER:
                case ExpressionType.CONSTANT:
                    return expr.val ();
                case ExpressionType.VARIABLE:
                    return double.NAN;
                case ExpressionType.UNARY: return unary (expr);
                case ExpressionType.BINARY: return binary (expr);
                case ExpressionType.POSTFIX: return postfix (expr);
                case ExpressionType.FUNCTION: return function (expr);
                default: assert_not_reached ();
            }
        }

        private double unary (Expression expr) {
            double v = eval (expr.right ());

            switch (expr.op ()) {
                case Operator.SUB: return -v;
                default: assert_not_reached ();
            }
        }

        private double binary (Expression expr) {
            double l = eval (expr.left ());
            double r = eval (expr.right ());

            switch (expr.op ()) {
                case Operator.ADD: return l + r;
                case Operator.SUB: return l - r;
                case Operator.MUL: return l * r;
                case Operator.POW: return Math.pow (l, r);
                case Operator.SUPERSCRIPT: return ipow (l, (int) r);

                case Operator.DIV:
                    if (r == 0) return double.NAN;
                    return l / r;

                default: assert_not_reached ();
            }
        }

        private double postfix (Expression expr) {
            double v = eval (expr.left ());

            switch (expr.op ()) {
                case Operator.FACT:
                    if (v < 0 || v != Math.floor (v)) return double.NAN;
                    return factorial (v);
                default: assert_not_reached ();
            }
        }

        private const double DEGREES_TO_RADIANS = 0.017453292519943295; // pi/180
        private const double RADIANS_TO_DEGREES = 57.29577951308232; // 180/pi

        private double function (Expression expr) {
            double x = eval (expr.right ());

            switch (expr.ident ()) {
                // trig radians
                case Ident.SIN: return Math.sin (x);
                case Ident.COS: return Math.cos (x);
                case Ident.TAN: return Math.tan (x);
                case Ident.COT: return 1d / Math.tan (x);
                case Ident.SEC: return 1d / Math.cos (x);
                case Ident.CSC: return 1d / Math.sin (x);

                // trig degrees
                case Ident.SIND: return Math.sin (x * DEGREES_TO_RADIANS);
                case Ident.COSD: return Math.cos (x * DEGREES_TO_RADIANS);
                case Ident.TAND: return Math.tan (x * DEGREES_TO_RADIANS);
                case Ident.COTD: return 1d / Math.tan (x * DEGREES_TO_RADIANS);
                case Ident.SECD: return 1d / Math.cos (x * DEGREES_TO_RADIANS);
                case Ident.CSCD: return 1d / Math.sin (x * DEGREES_TO_RADIANS);

                // inverse trig radians
                case Ident.ASIN: return Math.asin (x);
                case Ident.ACOS: return Math.acos (x);
                case Ident.ATAN: return Math.atan (x);
                case Ident.ACOT: return Math.asin (1d / Math.sqrt (1 + x * x));
                case Ident.ASEC: return Math.acos (1d / x);
                case Ident.ACSC: return Math.asin (1d / x);

                // inverse trig degrees
                case Ident.ASIND: return Math.asin (x) * RADIANS_TO_DEGREES;
                case Ident.ACOSD: return Math.acos (x) * RADIANS_TO_DEGREES;
                case Ident.ATAND: return Math.atan (x) * RADIANS_TO_DEGREES;
                case Ident.ACOTD: return Math.asin (1d / Math.sqrt (1 + x * x)) * RADIANS_TO_DEGREES;
                case Ident.ASECD: return Math.acos (1d / x) * RADIANS_TO_DEGREES;
                case Ident.ACSCD: return Math.asin (1d / x) * RADIANS_TO_DEGREES;

                // misc
                case Ident.LN: return Math.log (x);
                case Ident.LOG2: return Math.log2 (x);
                case Ident.LOG10: return Math.log10 (x);
                case Ident.SQRT: return Math.sqrt (x);
                case Ident.EXP: return Math.exp (x);
                case Ident.ABS: return Math.fabs (x);

                default: assert_not_reached ();
            }
        }
    }
}
