// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * Try evaluating a string to a double.
     * returns true if successfully parsed.
     */
    public static bool try_evaluate_string (string expression, out double? result = null, unichar decimal_separator = '.') {
        try {
            var ast = MathParser.Parser.instance ().parse (expression, decimal_separator);
            result = MathParser.Evaluator.instance ().eval_ast (ast);
            return true;
        } catch (Error e) {
            result = 0;
            return false;
        }
    }

    /**
     * Evaluate a string to a double.
     */
    public static double evaluate_string (string expression) throws MathError {
        var ast = MathParser.Parser.instance ().parse (expression);
        return MathParser.Evaluator.instance ().eval_ast (ast);
    }

    /**
     * Parse an Expression from string to an AST.
     */
    public static Ast expression_to_ast (string expression) throws MathError {
        return MathParser.Parser.instance ().parse (expression);
    }

    /**
     * Convert an AST to a string
     */
    public static string ast_to_expression (Ast expression) throws MathError {
        return MathParser.Printer.instance ().print (expression);
    }

    /**
     * Convert an AST to an executable array program.
     */
    public static Program ast_to_program (Ast expression, string variable = "x") throws MathError {
        Ast simplified = PythonHelper.simplify_expression (expression);
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
