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
                default:
                    throw new MathError.SYNTAX ("invalid token");
            }
        }
    }

    [Compact]
    private class Token {
        public TokenType type;
        public string text;
        public double val;

        public Token (TokenType type, string text = "", double val = 0) {
            this.type = type;
            this.text = text;
            this.val = val;
        }
    }

    private class MathParser {
        private string src;
        private int pos = 0;
        private Token current;

        public MathParser (string src) throws MathError {
            this.src = src.down ();
            next ();
        }

        public double parse () throws MathError {
            return expr ();
        }

        private void next () throws MathError {
            skip ();
            if (pos >= src.length) {
                current = new Token (TokenType.END);
                return;
            }

            int idx = pos;
            unichar c;
            if (!src.get_next_char (ref idx, out c)) {
                current = new Token (TokenType.END);
                return;
            }

            // Number
            if (c.isdigit () || c == '.') {
                int start = pos;
                while (idx <= src.length) {
                    unichar d;
                    int temp_idx = idx;
                    if (!src.get_next_char (ref temp_idx, out d) || !(d.isdigit () || d == '.'))
                        break;
                    idx = temp_idx;
                }

                string n = src.substring (start, idx - start);
                current = new Token (TokenType.NUMBER, n, double.parse (n));
                pos = idx;
                return;
            }

            // Identifier
            if (c.isalpha () || c == 'π' || c == 'e') {
                int start = pos;
                while (idx <= src.length) {
                    unichar d;
                    int temp_idx = idx;
                    if (!src.get_next_char (ref temp_idx, out d) || !(d.isalnum () || d == 'π'))
                        break;
                    idx = temp_idx;
                }

                current = new Token (TokenType.IDENT, src.substring (start, idx - start));
                pos = idx;
                return;
            }

            // Superscript
            int superscript_value = superscript_to_int (c);
            if (superscript_value >= 0) {
                current = new Token (TokenType.SUPERSCRIPT, c.to_string (), superscript_value);
                pos = idx;
                return;
            }

            // Single-character token
            pos = idx;
            current = new Token (TokenType.parse (c));
        }

        private void skip () {
            while (pos < src.length) {
                int idx = pos;
                unichar c;
                if (!src.get_next_char (ref idx, out c) || !c.isspace ())
                    break;
                pos = idx;
            }
        }

        public void expect_end () throws MathError {
            if (current.type != TokenType.END)
                throw new MathError.SYNTAX ("trailing input");
        }

        private void expect (TokenType t) throws MathError {
            if (current.type != t)
                throw new MathError.SYNTAX ("expected token");
            next ();
        }

        private int factorial (int n) {
            int r = 1;
            for (int i = 2; i <= n; i++)
                r *= i;
            return r;
        }

        private bool starts_value (Token t) {
            return t.type == TokenType.NUMBER
                || t.type == TokenType.IDENT
                || t.type == TokenType.LPAREN;
        }

        /* Grammar:
           expr  -> term ((+|-) term)*
           term  -> power ((*|/) power)*
           power -> unary ((^|**) power)?
           unary -> (- unary) | postfix
           postfix -> primary (!)*
           primary -> number | constant | func | '(' expr ')'
        */

        private double expr () throws MathError {
            double v = term ();
            while (current.type == TokenType.PLUS || current.type == TokenType.MINUS) {
                var t = current.type;
                next ();
                double r = term ();
                v = (t == TokenType.PLUS) ? v + r : v - r;
            }
            return v;
        }

        private double term () throws MathError {
            double v = power ();

            while (true) {
                /* explicit * or / */
                if (current.type == TokenType.STAR || current.type == TokenType.SLASH) {
                    var t = current.type;
                    next ();
                    double r = power ();
                    if (t == TokenType.SLASH && r == 0)
                        throw new MathError.DIV_ZERO ("division by zero");
                    v = (t == TokenType.STAR) ? v * r : v / r;
                    continue;
                }

                /* implicit multiplication */
                if (starts_value (current)) {
                    double r = power ();
                    v *= r;
                    continue;
                }

                break;
            }

            return v;
        }

        private double power () throws MathError {
            double v = unary ();
            if (current.type == TokenType.CARET) {
                next ();
                v = Math.pow (v, power ());
            }
            return v;
        }

        private double unary () throws MathError {
            if (current.type == TokenType.MINUS) {
                next ();
                return -unary ();
            }
            return postfix ();
        }

        private double postfix () throws MathError {
            double v = primary ();

            while (true) {
                if (current.type == TokenType.FACT) {
                    if (v < 0 || v != Math.floor (v))
                        throw new MathError.DOMAIN ("invalid factorial");
                    v = factorial ((int) v);
                    next ();
                    continue;
                }

                if (current.type == TokenType.SUPERSCRIPT) {
                    int exp = (int) current.val;
                    next ();
                    v = Math.pow (v, exp);
                    continue;
                }

                break;
            }
            return v;
        }

        private double primary () throws MathError {
            if (current.type == TokenType.NUMBER) {
                double v = current.val;
                next ();
                return v;
            }

            if (current.type == TokenType.IDENT) {
                string name = current.text;
                next ();

                if (name == "pi" || name == "π")
                    return Math.PI;

                if (name == "e")
                    return Math.E;

                if (current.type == TokenType.LPAREN) {
                    next ();
                    double arg = expr ();
                    expect (TokenType.RPAREN);

                    return call_function (name, arg);
                }

                throw new MathError.UNKNOWN_FUNCTION (name);
            }

            if (current.type == TokenType.LPAREN) {
                next ();
                double v = expr ();
                expect (TokenType.RPAREN);
                return v;
            }

            throw new MathError.SYNTAX ("unexpected token");
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
