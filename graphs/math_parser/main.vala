// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * Try evaluating a string to a double.
     * returns true if successfully parsed.
     */
    public static bool try_evaluate_string (string expression, out double? result = null, unichar decimal_separator = '.') {
        try {
            var ast = MathParser.Parser.instance ().parse (expression, decimal_separator);
            result = MathParser.Evaluator.instance ().eval (ast);
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
        var ast = MathParser.Parser.instance ().parse (expression);
        return MathParser.Evaluator.instance ().eval (ast);
    }

    // This method exists separately as optional arguments are not automatically
    // bound by python
    /**
     * Evaluate a string to a double with given decimal separator.
     */
    public static double evaluate_string_with_separator (string expression, unichar separator) throws MathError {
        var ast = MathParser.Parser.instance ().parse (expression, separator);
        return MathParser.Evaluator.instance ().eval (ast);
    }

    /**
     * Preprocess an equation to be compatible with numexpr syntax.
     */
    public static string preprocess_equation (string equation) throws MathError {
        var ast = MathParser.Parser.instance ().parse (equation);
        return MathParser.Printer.instance ().print (ast);
    }

    /**
     * Return an equation in a prettier, more humanly readable, format.
     */
    public static string prettify_equation (string equation) throws MathError {
        var ast = MathParser.Parser.instance ().parse (equation);
        string result = MathParser.Printer.instance ().print (ast, true);

        // remove asterisk between parentheses
        result = result.replace (")*(", "()");

        return result;
    }

    public errordomain MathError {
        SYNTAX,
        UNKNOWN_FUNCTION,
        DOMAIN,
        DIV_ZERO
    }

    namespace MathParser {
        private enum TokenType {
            NUMBER,
            IDENT,
            PLUS, MINUS, STAR, SLASH,
            CARET,
            FACT,
            SUPERSCRIPT,
            LPAREN, RPAREN,
            END
        }

        private enum Ident {
            // constants
            PI,
            E,
            INF,

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
            ABS,

            CUSTOM
        }

        private abstract class Expression {}

        private class NumberExpression : Expression {
            public double val;
            public NumberExpression (double v) { val = v; }
        }

        private class VariableExpression : Expression {
            public string name;
            public VariableExpression (string n) { name = n; }
        }

        private class UnaryExpression : Expression {
            public TokenType op;
            public Expression expr;
            public UnaryExpression (TokenType op, Expression e) {
                this.op = op;
                this.expr = e;
            }
        }

        private class BinaryExpression : Expression {
            public TokenType op;
            public Expression left;
            public Expression right;

            public BinaryExpression (Expression l, TokenType op, Expression r) {
                this.left = l;
                this.op = op;
                this.right = r;
            }
        }

        private class FunctionExpression : Expression {
            public Ident ident;
            public Expression arg;

            public FunctionExpression (Ident id, Expression arg) {
                this.ident = id;
                this.arg = arg;
            }
        }

        private class PostfixExpression : Expression {
            public Expression expr;
            public TokenType op;

            public PostfixExpression (Expression e, TokenType op) {
                this.expr = e;
                this.op = op;
            }
        }

        private static inline long factorial (int n) {
            long r = 1;
            for (int i = 2; i <= n; i++)
                r *= i;
            return r;
        }

        private static inline double ipow (double bas, int exp) {
            double result = 1;
            double b = bas;
            int e = exp;

            while (e > 0) {
                if ((e & 1) == 1) result *= b;
                b = b * b;
                e >>= 1;
            }

            return result;
        }

        private static inline bool is_superscript (unichar c) {
            switch (c) {
                case '⁰': case '¹': case '²': case '³': case '⁴': case '⁵':
                case '⁶': case '⁷': case '⁸': case '⁹': return true;
                default: return false;
            }
        }
    }
}
