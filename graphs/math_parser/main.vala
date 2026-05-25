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
     * Parse an Expression from string to an AST.
     */
    public static Expression expression_to_ast (string expression) throws MathError {
        return MathParser.Parser.instance ().parse (expression);
    }

    /**
     * Convert an AST to a string
     */
    public static string ast_to_expression (Expression expression) throws MathError {
        return MathParser.Printer.instance ().print (expression, true);
    }

    /**
     * Convert an AST to a string compatible with numexpr syntax
     */
    public static string ast_to_numexpr (Expression expression) throws MathError {
        return MathParser.Printer.instance ().print (expression, false);
    }

    /**
     * Evaluate an AST to a double array.
     */
    public static double[] evaluate_expression_array (Expression expression, double[] xdata, string variable = "x") throws MathError {
        var program = MathParser.Compiler.instance ().compile (expression, variable);
        double[] ydata = new double[xdata.length];
        MathParser.eval_array (program, xdata, ydata);
        return ydata;
    }

    namespace MathParser {
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

        [CCode (cname = "eval_array", cheader_filename = "math_parser/array_evaluator.h")]
        private extern void eval_array (
            [CCode (array_length = true)]
            Instruction[] program,
            [CCode (array_length = true)]
            double[] xdata,
            [CCode (array_length = true)]
            double[] ydata
        );
    }
}
