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
        return MathParser.Printer.instance ().print (expression);
    }

    /**
     * Convert an AST to an executable array program.
     */
    public static Program ast_to_program (Expression expression, string variable = "x") throws MathError {
        Expression simplified = PythonHelper.simplify_expression (expression);
        return MathParser.Compiler.instance ().compile (simplified, variable);
    }

    namespace MathParser {
        [CCode (cname = "factorial", cheader_filename = "math_parser/array_evaluator.h")]
        private extern double factorial (double x);

        [CCode (cname = "ipow", cheader_filename = "math_parser/array_evaluator.h")]
        private extern double ipow (double base, int exp);

        [CCode (cname = "eval_array", cheader_filename = "math_parser/array_evaluator.h")]
        private extern void eval_array (
            [CCode (array_length = false)]
            OpCode[] program,
            [CCode (array_length = false)]
            double[] data,
            size_t plen,
            [CCode (array_length = false)]
            double[] xdata,
            [CCode (array_length = false)]
            double[] ydata,
            size_t n
        );
    }
}
