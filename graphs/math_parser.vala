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

    private int superscript_to_int (unichar c) {
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

    private class MathParser {
        private string src;
        private int pos = 0;

        private TokenType current_type;
        private string current_text;

        public MathParser (string src) throws MathError {
            this.src = src.down ();
            next ();
        }

        public double parse () throws MathError {
            return expr ();
        }

        private void next () throws MathError {
            skip ();
            int idx = pos;
            unichar c;
            if (!src.get_next_char (ref idx, out c)) {
                current_type = TokenType.END;
                return;
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
                current_text = superscript_value.to_string ();
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

            while (true) {
                if (c.isdigit ()) {
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
                        int sign_idx = tmp_idx;
                        if (!src.get_next_char (ref sign_idx, out c))
                            break;
                        tmp_idx = sign_idx;
                    }

                    // Must have at least one digit to be an exponent
                    if (!c.isdigit ()) break;
                    seen_exp = true;
                    last_is_dot = false;
                } else break;

                // advance to next character
                idx = tmp_idx;
                if (!src.get_next_char (ref tmp_idx, out c)) break;
            }

            // must contain at least one digit and must not have a trailing dot
            if (last_is_dot) throw new MathError.SYNTAX ("invalid number");

            current_type = TokenType.NUMBER;
            current_text = src.substring (pos, idx - pos);
            pos = idx;
        }

        private void handle_identifier (ref int idx, ref unichar c) {
            int tmp_idx = idx;
            while (idx <= src.length) {
                if (!src.get_next_char (ref tmp_idx, out c) || !(c.isalnum () || c == 'π'))
                    break;
                idx = tmp_idx;
            }

            current_type = TokenType.IDENT;
            current_text = src.substring (pos, idx - pos);
            pos = idx;
        }

        private void skip () {
            int idx = pos;
            while (pos < src.length) {
                unichar c;
                if (!src.get_next_char (ref idx, out c) || !c.isspace ()) break;
                pos = idx;
            }
        }

        public void expect_end () throws MathError {
            if (current_type != TokenType.END)
                throw new MathError.SYNTAX ("trailing input");
        }

        private void expect (TokenType t) throws MathError {
            if (current_type != t)
                throw new MathError.SYNTAX ("expected token");
            next ();
        }

        private int factorial (int n) {
            int r = 1;
            for (int i = 2; i <= n; i++)
                r *= i;
            return r;
        }

        private bool starts_value (TokenType t) {
            return t == TokenType.NUMBER
                || t == TokenType.IDENT
                || t == TokenType.LPAREN;
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
                if (starts_value (t)) {
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
                    int exp = int.parse (current_text);
                    next ();
                    v = Math.pow (v, exp);
                    continue;
                }

                break;
            }
            return v;
        }

        private double primary () throws MathError {
            switch (current_type) {
                case TokenType.NUMBER:
                    double v = double.parse (current_text);
                    next ();
                    return v;
                case TokenType.IDENT:
                    string text = current_text;
                    next ();

                    if (text == "pi" || text == "π")
                        return Math.PI;

                    if (text == "e")
                        return Math.E;

                    if (current_type == TokenType.LPAREN) {
                        next ();
                        double arg = expr ();
                        expect (TokenType.RPAREN);

                        return call_function (text, arg);
                    }
                    throw new MathError.UNKNOWN_FUNCTION (text);
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

        private double call_function (string f, double x) throws MathError {
            try {
                return trig_function (f, x);
            } catch (MathError.UNKNOWN_FUNCTION e) {}

            switch (f) {
                case "log": return Math.log (x);
                case "log2": return Math.log2 (x);
                case "log10": return Math.log10 (x);

                case "sqrt": return Math.sqrt (x);
                case "exp": return Math.exp (x);
                case "abs": return Math.fabs (x);
            }

            throw new MathError.UNKNOWN_FUNCTION (f);
        }

        private double trig_function (owned string f, double x) throws MathError {
            if (f.has_suffix ("d")) {
                f = f.substring (0, f.length - 1);
                x = x * DEGREES_TO_RADIANS;
            }

            switch (f) {
                case "sin": return Math.sin (x);
                case "cos": return Math.cos (x);
                case "tan": return Math.tan (x);
                case "cot": return 1d / Math.tan (x);
                case "sec": return 1d / Math.cos (x);
                case "csc": return 1d / Math.sin (x);

                case "arcsin": case "asin": return Math.asin (x);
                case "arccos": case "acos": return Math.acos (x);
                case "arctan": case "atan": return Math.atan (x);
                case "arccot": case "acot": return Math.asin (1d / Math.sqrt (1 + x * x));
                case "arcsec": case "asec": return Math.acos (1d / x);
                case "arccsc": case "acsc": return Math.asin (1d / x);
            }

            throw new MathError.UNKNOWN_FUNCTION (f);
        }
    }
}
