// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public static bool try_evaluate_string (string expression, out double? result = null) {
        if (expression.strip ().length == 0) {
            result = 0;
            return false;
        }

        if (double.try_parse (expression, out result)) {
            return true;
        }

        try {
            var parser = new MathParser (expression);
            result = parser.parse ();
            parser.expect_end ();
            return true;
        } catch (Error e) {
            return false;
        }
    }

    public static double evaluate_string (string expression) throws MathError {
        double result;
        if (double.try_parse (expression, out result)) {
            return result;
        }

        var parser = new MathParser (expression);
        result = parser.parse ();
        parser.expect_end ();
        return result;
    }

    public errordomain MathError {
        SYNTAX,
        UNKNOWN_FUNCTION,
        DOMAIN,
        DIV_ZERO
    }

    enum TokenType {
        NUMBER,
        IDENT,
        PLUS, MINUS, STAR, SLASH,
        CARET,
        FACT,
        LPAREN, RPAREN,
        END;

        public static TokenType parse (char c) {
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

    class Token {
        public TokenType type;
        public string text;
        public double val;

        public Token (TokenType type, string text = "", double val = 0) {
            this.type = type;
            this.text = text;
            this.val = val;
        }
    }

    class MathParser {
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

            char c = src[pos];

            if (c.isdigit () || c == '.') {
                int start = pos;
                while (pos < src.length &&
                       (src[pos].isdigit () || src[pos] == '.'))
                    pos++;
                string n = src.substring (start, pos - start);
                current = new Token (TokenType.NUMBER, n, double.parse (n));
                return;
            }

            if (c.isalpha () || c == 'π') {
                int start = pos;
                while (pos < src.length &&
                       (src[pos].isalnum () || src[pos] == 'π'))
                    pos++;
                current = new Token (TokenType.IDENT,
                                     src.substring (start, pos - start));
                return;
            }

            pos++;
            current = new Token (TokenType.parse (c));
        }

        private void skip () {
            while (pos < src.length && src[pos].isspace ())
                pos++;
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
            while (current.type == TokenType.FACT) {
                if (v < 0 || v != Math.floor (v))
                    throw new MathError.DOMAIN ("invalid factorial");
                v = factorial ((int) v);
                next ();
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

        private double call_function (owned string f, double x) throws MathError {
            bool deg = f.has_suffix ("d");
            if (deg) {
                f = f.substring (0, f.length - 1);
                x = x * Math.PI / 180.0;
            }

            switch (f) {
                case "sin": return Math.sin (x);
                case "cos": return Math.cos (x);
                case "tan": return Math.tan (x);
                case "cot": return 1.0 / Math.tan (x);
                case "sec": return 1.0 / Math.cos (x);
                case "csc": return 1.0 / Math.sin (x);

                case "arcsin": return Math.asin (x);
                case "arccos": return Math.acos (x);
                case "arctan": return Math.atan (x);
                case "arccot": return Math.asin (1.0 / Math.sqrt (1 + x * x));
                case "arcsec": return Math.acos (1.0 / x);
                case "arccsc": return Math.asin (1.0 / x);
            }

            throw new MathError.UNKNOWN_FUNCTION (f);
        }
    }
}
