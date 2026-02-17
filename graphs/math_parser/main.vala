// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * Try evaluating a string to a double.
     * returns true if successfully parsed.
     */
    public static bool try_evaluate_string (string expression, out double? result = null, unichar decimal_separator = '.') {
        try {
            result = MathParser.Evaluator.instance ().parse (expression, decimal_separator);
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
        return MathParser.Evaluator.instance ().parse (expression);
    }

    // This method exists separately as optional arguments are not automatically
    // bound by python
    /**
     * Evaluate a string to a double with given decimal separator.
     */
    public static double evaluate_string_with_separator (string expression, unichar separator) throws MathError {
        return MathParser.Evaluator.instance ().parse (expression, separator);
    }

    /**
     * Preprocess an equation to be compatible with numexpr syntax.
     */
    public static string preprocess_equation (string equation) throws MathError {
        return MathParser.Preprocessor.instance ().preprocess (equation);
    }

    /**
     * Return an equation in a prettier, more humanly readable, format.
     */
    public static string prettify_equation (string equation) throws MathError {
        return MathParser.Preprocessor.instance ().preprocess (equation, true).replace (")*(", "()");
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
