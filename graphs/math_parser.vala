// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * Try evaluating a string to a double.
     * returns true if successfully parsed.
     */
    public static bool try_evaluate_string (string expression, out double? result = null) {
        if (expression.strip ().length == 0) {
            result = 0;
            return false;
        }

        try {
            var parser = new MathParser (expression);
            result = parser.parse ();
            parser.expect_end ();
            return true;
        } catch (Error e) {
            result = 0;
            return false;
        }
    }

    // This method exists primarily to be used on the python side. Do note that
    // the potential MathError is intentional here as returning double? or using
    // an out variable leads to issues when automatically generating a binding.
    // with the compromise being, that the MathError has to be handled on the
    // python side when consuming this method.
    /**
     * Evaluate a string to a double.
     */
    public static double evaluate_string (string expression) throws MathError {
        if (expression.strip ().length == 0) {
            throw new MathError.SYNTAX ("empty expression");
        }

        var parser = new MathParser (expression);
        double result = parser.parse ();
        parser.expect_end ();
        return result;
    }

    public errordomain MathError {
        SYNTAX,
        UNKNOWN_FUNCTION,
        DOMAIN,
        DIV_ZERO
    }

    private inline int superscript_to_int (unichar c) {
        switch (c) {
            case '⁰': return 0;
            case '¹': return 1;
            case '²': return 2;
            case '³': return 3;
            case '⁴': return 4;
            case '⁵': return 5;
            case '⁶': return 6;
            case '⁷': return 7;
            case '⁸': return 8;
            case '⁹': return 9;
            default: return -1;
        }
    }

    private enum TokenType {
        NUMBER,
        IDENT,
        PLUS, MINUS, STAR, SLASH,
        CARET,
        FACT,
        SUPERSCRIPT,
        LPAREN, RPAREN,
        END;

        public static TokenType parse (unichar c) throws MathError {
            if (superscript_to_int (c) >= 0) return TokenType.SUPERSCRIPT;
            switch (c) {
                case '+': return TokenType.PLUS;
                case '-': return TokenType.MINUS;
                case '*': return TokenType.STAR;
                case '/': return TokenType.SLASH;
                case '^': return TokenType.CARET;
                case '!': return TokenType.FACT;
                case '(': return TokenType.LPAREN;
                case ')': return TokenType.RPAREN;
                default: throw new MathError.SYNTAX ("invalid token");
            }
        }
    }

    private enum Ident {
        // constants
        PI,
        E,

        // trig
        SIN, COS, TAN, COT, SEC, CSC,
        SIND, COSD, TAND, COTD, SECD, CSCD,

        // inverse trig
        ASIN, ACOS, ATAN, ACOT, ASEC, ACSC,
        ASIND, ACOSD, ATAND, ACOTD, ASECD, ACSCD,

        // misc math
        LOG,
        LOG2,
        LOG10,
        SQRT,
        EXP,
        ABS;

        public static Ident parse (string s) throws MathError {
            switch (s) {
                // constants
                case "pi": case "π": return Ident.PI;
                case "e": return Ident.E;

                // trig radians
                case "sin": return Ident.SIN;
                case "cos": return Ident.COS;
                case "tan": return Ident.TAN;
                case "cot": return Ident.COT;
                case "sec": return Ident.SEC;
                case "csc": return Ident.CSC;

                // trig degrees
                case "sind": return Ident.SIND;
                case "cosd": return Ident.COSD;
                case "tand": return Ident.TAND;
                case "cotd": return Ident.COTD;
                case "secd": return Ident.SECD;
                case "cscd": return Ident.CSCD;

                // inverse trig radians
                case "asin": case "arcsin": return Ident.ASIN;
                case "acos": case "arccos": return Ident.ACOS;
                case "atan": case "arctan": return Ident.ATAN;
                case "acot": case "arccot": return Ident.ACOT;
                case "asec": case "arcsec": return Ident.ASEC;
                case "acsc": case "arccsc": return Ident.ACSC;

                // inverse trig degrees
                case "asind": case "arcsind": return Ident.ASIND;
                case "acosd": case "arccosd": return Ident.ACOSD;
                case "atand": case "arctand": return Ident.ATAND;
                case "acotd": case "arccotd": return Ident.ACOTD;
                case "asecd": case "arcsecd": return Ident.ASECD;
                case "acscd": case "arccscd": return Ident.ACSCD;

                // misc
                case "log": return Ident.LOG;
                case "log2": return Ident.LOG2;
                case "log10": return Ident.LOG10;
                case "sqrt": return Ident.SQRT;
                case "exp": return Ident.EXP;
                case "abs": return Ident.ABS;

                default: throw new MathError.UNKNOWN_FUNCTION (s);
            }
        }
    }

    private class MathParser {
        private string src;
        private int pos = 0;

        private TokenType current_type;
        private Ident current_ident;
        private double current_val;

        public MathParser (string src) throws MathError {
            this.src = src.down ();
            next ();
        }

        public double parse () throws MathError {
            return expr ();
        }

        private void next () throws MathError {
            int idx = pos;
            unichar c;
            while (true) {
                if (!src.get_next_char (ref idx, out c)) {
                    current_type = TokenType.END;
                    return;
                }
                if (!c.isspace ()) break;
                pos = idx;
            }

            // Number
            if (c.isdigit () || c == '.') {
                handle_number (ref idx, ref c);
                return;
            }

            // Identifier
            if (c.isalpha () || c == 'π') {
                handle_identifier (ref idx, ref c);
                return;
            }

            // Superscript
            int superscript_value = superscript_to_int (c);
            if (superscript_value >= 0) {
                current_type = TokenType.SUPERSCRIPT;
                current_val = superscript_value;
                pos = idx;
                return;
            }

            // Single-character token
            current_type = TokenType.parse (c);
            pos = idx;
        }

        private void handle_number (ref int idx, ref unichar c) throws MathError {
            bool seen_dot = false;
            bool last_is_dot = false;
            bool seen_exp = false;
            int tmp_idx = idx;

            int int_part = 0;
            int frac_part = 0;
            int frac_digits = 0;
            int exp = 0;
            int exp_sign = 1;

            int digit;
            int sign_idx;

            while (true) {
                if (c.isdigit ()) {
                    digit = (int) (c - '0');

                    if (seen_exp) {
                        exp = exp * 10 + digit;
                    } else if (seen_dot) {
                        frac_part = frac_part * 10 + digit;
                        frac_digits++;
                    } else {
                        int_part = int_part * 10 + digit;
                    }

                    last_is_dot = false;
                } else if (c == '.') {
                    if (seen_dot || seen_exp)
                        throw new MathError.SYNTAX ("invalid number");
                    seen_dot = true;
                    last_is_dot = true;
                } else if (c == 'e' && !seen_exp) {
                    // Look ahead to see if this is really an exponent
                    if (!src.get_next_char (ref tmp_idx, out c)) break;

                    // Optional sign
                    if (c == '+' || c == '-') {
                        if (c == '-') exp_sign = -1;
                        sign_idx = tmp_idx;
                        if (!src.get_next_char (ref sign_idx, out c))
                            break;
                        tmp_idx = sign_idx;
                    }

                    // Must have at least one digit to be an exponent
                    if (!c.isdigit ()) break;
                    seen_exp = true;
                    last_is_dot = false;
                    idx = tmp_idx;
                    continue;
                } else break;

                // advance to next character
                idx = tmp_idx;
                if (!src.get_next_char (ref tmp_idx, out c)) break;
            }

            // must contain at least one digit and must not have a trailing dot
            if (last_is_dot) throw new MathError.SYNTAX ("invalid number");

            double val = int_part;
            if (seen_dot) val += frac_part / ipow (10d, frac_digits);
            if (seen_exp) {
                int e = exp_sign * exp;
                val *= (e >= 0 && e <= 308) ? ipow (10d, e) : Math.pow (10d, e);
            }

            current_type = TokenType.NUMBER;
            current_val = val;
            pos = idx;
        }

        private void handle_identifier (ref int idx, ref unichar c) throws MathError {
            int tmp_idx = idx;
            while (true) {
                if (!src.get_next_char (ref tmp_idx, out c) || !(c.isalnum () || c == 'π'))
                    break;
                idx = tmp_idx;
            }

            current_type = TokenType.IDENT;
            current_ident = Ident.parse (src.substring (pos, idx - pos));
            pos = idx;
        }

        public void expect_end () throws MathError {
            if (current_type != TokenType.END)
                throw new MathError.SYNTAX ("trailing input");
        }

        private inline void expect (TokenType t) throws MathError {
            if (current_type != t)
                throw new MathError.SYNTAX ("expected token");
            next ();
        }

        private inline int factorial (int n) {
            int r = 1;
            for (int i = 2; i <= n; i++)
                r *= i;
            return r;
        }

        private double ipow (double bas, int exp) {
            double result = 1;
            double b = bas;
            int e = exp;

            while (e > 0) {
                if ((e & 1) == 1) result *= b;
                b = b*b;
                e >>= 1;
            }

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
            while (current_type == TokenType.PLUS || current_type == TokenType.MINUS) {
                var t = current_type;
                next ();
                double r = term ();
                v = (t == TokenType.PLUS) ? v + r : v - r;
            }
            return v;
        }

        private double term () throws MathError {
            double v = power ();

            while (true) {
                TokenType t = current_type;
                // explicit * or /
                if (t == TokenType.STAR || t == TokenType.SLASH) {
                    next ();
                    double r = power ();
                    if (t == TokenType.SLASH && r == 0)
                        throw new MathError.DIV_ZERO ("division by zero");
                    v = (t == TokenType.STAR) ? v * r : v / r;
                    continue;
                }

                // implicit multiplication
                if (t == TokenType.NUMBER || t == TokenType.IDENT || t == TokenType.LPAREN) {
                    v *= expr ();
                }
                break;
            }

            return v;
        }

        private double power () throws MathError {
            double v = unary ();
            if (current_type == TokenType.CARET) {
                next ();
                v = Math.pow (v, power ());
            }
            return v;
        }

        private double unary () throws MathError {
            if (current_type == TokenType.MINUS) {
                next ();
                return -unary ();
            }
            return postfix ();
        }

        private double postfix () throws MathError {
            double v = primary ();

            while (true) {
                if (current_type == TokenType.FACT) {
                    if (v < 0 || v != Math.floor (v))
                        throw new MathError.DOMAIN ("invalid factorial");
                    v = factorial ((int) v);
                    next ();
                    continue;
                }

                if (current_type == TokenType.SUPERSCRIPT) {
                    int exp = (int) current_val;
                    next ();
                    v = ipow (v, exp);
                    continue;
                }

                break;
            }
            return v;
        }

        private double primary () throws MathError {
            switch (current_type) {
                case TokenType.NUMBER:
                    double v = current_val;
                    next ();
                    return v;
                case TokenType.IDENT:
                    Ident id = current_ident;
                    next ();

                    switch (id) {
                        case Ident.PI: return Math.PI;
                        case Ident.E: return Math.E;
                        default: break;
                    }

                    expect (TokenType.LPAREN);
                    double arg = expr ();
                    expect (TokenType.RPAREN);

                    return call_function (id, arg);
                case TokenType.LPAREN:
                    next ();
                    double v = expr ();
                    expect (TokenType.RPAREN);
                    return v;
                default:
                    throw new MathError.SYNTAX ("unexpected token");
            }
        }

        private const double DEGREES_TO_RADIANS = Math.PI / 180d;

        private double call_function (Ident id, double x) {
            switch (id) {
                // trig radians
                case Ident.SIN: return Math.sin(x);
                case Ident.COS: return Math.cos(x);
                case Ident.TAN: return Math.tan(x);
                case Ident.COT: return 1d / Math.tan(x);
                case Ident.SEC: return 1d / Math.cos(x);
                case Ident.CSC: return 1d / Math.sin(x);

                // trig degrees
                case Ident.SIND: return Math.sin(x * DEGREES_TO_RADIANS);
                case Ident.COSD: return Math.cos(x * DEGREES_TO_RADIANS);
                case Ident.TAND: return Math.tan(x * DEGREES_TO_RADIANS);
                case Ident.COTD: return 1d / Math.tan(x * DEGREES_TO_RADIANS);
                case Ident.SECD: return 1d / Math.cos(x * DEGREES_TO_RADIANS);
                case Ident.CSCD: return 1d / Math.sin(x * DEGREES_TO_RADIANS);

                // inverse trig radians
                case Ident.ASIN: return Math.asin(x);
                case Ident.ACOS: return Math.acos(x);
                case Ident.ATAN: return Math.atan(x);
                case Ident.ACOT: return Math.asin(1d / Math.sqrt(1 + x*x));
                case Ident.ASEC: return Math.acos(1d / x);
                case Ident.ACSC: return Math.asin(1d / x);

                // inverse trig degrees
                case Ident.ASIND: return Math.asin(x * DEGREES_TO_RADIANS);
                case Ident.ACOSD: return Math.acos(x * DEGREES_TO_RADIANS);
                case Ident.ATAND: return Math.atan(x * DEGREES_TO_RADIANS);
                case Ident.ACOTD:
                    double x2 = x * DEGREES_TO_RADIANS;
                    return Math.asin(1d / Math.sqrt(1 + x2 * x2));
                case Ident.ASECD: return Math.acos(1d / x * DEGREES_TO_RADIANS);
                case Ident.ACSCD: return Math.asin(1d / x * DEGREES_TO_RADIANS);

                // misc
                case Ident.LOG: return Math.log(x);
                case Ident.LOG2: return Math.log2(x);
                case Ident.LOG10: return Math.log10(x);
                case Ident.SQRT: return Math.sqrt(x);
                case Ident.EXP: return Math.exp(x);
                case Ident.ABS: return Math.fabs(x);

                default: assert_not_reached ();
            }
        }
    }
}
