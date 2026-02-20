// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Evaluator {
        private Lexer lexer = new Lexer ();

        private static Once<Evaluator> _instance;

        public static unowned Evaluator instance () {
            return _instance.once (() => { return new Evaluator (); });
        }

        public double parse (string src, unichar decimal_separator = '.') throws MathError {
            lexer.start_lexing (src, decimal_separator);
            double result = expr ();
            lexer.expect_end ();
            return result;
        }

        /* Grammar:
           expr    -> term ((+|-) term)*
           term    -> power ((*|/) power)*
           term    -> power expr
           power   -> unary ((^|**) power)?
           unary   -> (- unary) | postfix
           postfix -> primary (!)*
           primary -> number | constant | func | '(' expr ')'
        */

        private double expr () throws MathError {
            double v = term ();
            TokenType t;
            while (true) {
                t = lexer.current_type;
                if (!(t == TokenType.PLUS || t == TokenType.MINUS)) break;
                lexer.next ();
                double r = term ();
                v = (t == TokenType.PLUS) ? v + r : v - r;
            }
            return v;
        }

        private double term () throws MathError {
            double v = power ();

            while (true) {
                TokenType t = lexer.current_type;
                // explicit * or /
                if (t == TokenType.STAR || t == TokenType.SLASH) {
                    lexer.next ();
                    double r = power ();
                    if (t == TokenType.SLASH && r == 0)
                        throw new MathError.DIV_ZERO ("division by zero");
                    v = (t == TokenType.STAR) ? v * r : v / r;
                    continue;
                }

                // implicit multiplication
                if (t == TokenType.NUMBER || t == TokenType.IDENT || t == TokenType.LPAREN) {
                    v *= power ();
                    continue;
                }
                break;
            }

            return v;
        }

        private double power () throws MathError {
            double v = unary ();
            if (lexer.current_type == TokenType.CARET) {
                lexer.next ();
                v = Math.pow (v, power ());
            }
            return v;
        }

        private double unary () throws MathError {
            if (lexer.current_type == TokenType.MINUS) {
                lexer.next ();
                return -postfix ();
            } else if (lexer.current_type == TokenType.PLUS) {
                lexer.next ();
            }
            return postfix ();
        }

        private double postfix () throws MathError {
            double v = primary ();

            while (true) {
                if (lexer.current_type == TokenType.FACT) {
                    if (v < 0 || v != Math.floor (v))
                        throw new MathError.DOMAIN ("invalid factorial");
                    v = factorial ((int) v);
                    lexer.next ();
                    continue;
                }

                if (lexer.current_type == TokenType.SUPERSCRIPT) {
                    int exp = (int) lexer.current_val;
                    lexer.next ();
                    v = ipow (v, exp);
                    continue;
                }

                break;
            }
            return v;
        }

        private double primary () throws MathError {
            switch (lexer.current_type) {
                case TokenType.NUMBER:
                    double v = lexer.current_val;
                    lexer.next ();
                    return v;
                case TokenType.IDENT:
                    Ident id = lexer.current_ident;
                    lexer.next ();

                    switch (id) {
                        case Ident.PI: return Math.PI;
                        case Ident.E: return Math.E;
                        case Ident.INF: return double.INFINITY;
                        default: break;
                    }

                    lexer.expect (TokenType.LPAREN);
                    double arg = expr ();
                    lexer.expect (TokenType.RPAREN);

                    return call_function (id, arg);
                case TokenType.LPAREN:
                    lexer.next ();
                    double v = expr ();
                    lexer.expect (TokenType.RPAREN);
                    return v;
                default:
                    throw new MathError.SYNTAX ("unexpected token");
            }
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
