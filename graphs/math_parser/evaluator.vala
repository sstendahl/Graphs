// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Evaluator {
        private static Once<Evaluator> _instance;

        public static unowned Evaluator instance () {
            return _instance.once (() => { return new Evaluator (); });
        }

        public double eval (Expression expr) throws MathError {
            if (expr is VariableExpression) return variable ((VariableExpression) expr);
            if (expr is NumberExpression) return number ((NumberExpression) expr);
            if (expr is ConstantExpression) return constant ((ConstantExpression) expr);
            if (expr is UnaryExpression) return unary ((UnaryExpression) expr);
            if (expr is BinaryExpression) return binary ((BinaryExpression) expr);
            if (expr is FunctionExpression) return function ((FunctionExpression) expr);
            if (expr is PostfixExpression) return postfix ((PostfixExpression) expr);

            assert_not_reached ();
        }

        private double number (NumberExpression expr) throws MathError {
            return expr.val;
        }

        private double constant (ConstantExpression expr) throws MathError {
            return expr.val ();
        }

        private double variable (VariableExpression expr) throws MathError {
            throw new MathError.UNKNOWN_FUNCTION ("variables not allowed");
        }

        private double unary (UnaryExpression expr) throws MathError {
            double v = eval (expr.expr);

            switch (expr.op) {
                case TokenType.MINUS: return -v;
                case TokenType.PLUS: return v;
                default: throw new MathError.SYNTAX ("invalid unary operator");
            }
        }

        private double binary (BinaryExpression expr) throws MathError {
            double l = eval (expr.left);
            double r = eval (expr.right);

            switch (expr.op) {
                case TokenType.PLUS: return l + r;
                case TokenType.MINUS: return l - r;
                case TokenType.STAR: return l * r;
                case TokenType.CARET: return Math.pow (l, r);
                case TokenType.SUPERSCRIPT: return ipow (l, (int) r);

                case TokenType.SLASH:
                    if (r == 0)
                        throw new MathError.DIV_ZERO ("division by zero");
                    return l / r;

                default: throw new MathError.SYNTAX ("invalid binary operator");
            }
        }

        private double postfix (PostfixExpression expr) throws MathError {
            double v = eval (expr.expr);

            switch (expr.op) {
                case TokenType.FACT:
                    if (v < 0 || v != Math.floor (v))
                        throw new MathError.DOMAIN ("invalid factorial");
                    return factorial ((int) v);
                default: throw new MathError.SYNTAX ("invalid postfix operator");
            }
        }

        private double function (FunctionExpression expr) throws MathError {
            double x = eval (expr.arg);
            return call_function (expr.ident, x);
        }

        private const double DEGREES_TO_RADIANS = 0.017453292519943295; // pi/180
        private const double RADIANS_TO_DEGREES = 57.29577951308232; // 180/pi

        private static double call_function (Ident id, double x) {
            switch (id) {
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
                case Ident.LOG: return Math.log (x);
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
