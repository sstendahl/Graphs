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
    public static Program ast_to_program (
        Ast expression, string variable = "x"
    ) throws MathError {
        Ast expr = PythonHelper.simplify_expression (expression);
        return MathParser.Compiler.instance ().compile (expr, variable);
    }

    /**
     * Convert an AST to an executable array program, with variables that
     * can be set afterwards.
     */
    public static Program ast_to_parametric_program (
        Ast expression, string variable = "x"
    ) throws MathError {
        Ast expr = PythonHelper.simplify_expression (expression);
        string[] names = MathTools.get_free_variables (ast_to_expression (expression));
        foreach (unowned string name in MathTools.get_free_variables (ast_to_expression (expr))) {
            if (!(name in names)) throw new MathError.UNKNOWN_FUNCTION ("invalid variable: " + name);
        }
        return MathParser.Compiler.instance ().compile (expr, variable, true);
    }

    private static Expression bind_expression (Expression expr, string name, double val) {
        switch (expr.type ()) {
            case ExpressionType.NUMBER:
                return new Expression.number (expr.val ());
            case ExpressionType.CONSTANT:
                return new Expression.constant (expr.ident ());
            case ExpressionType.VARIABLE:
                if (expr.name () != name) return new Expression.variable (expr.name ());
                return new Expression.number (val);
            case ExpressionType.UNARY:
                return new Expression.unary (expr.op (), bind_expression (expr.right (), name, val));
            case ExpressionType.BINARY:
                return new Expression.binary (
                    bind_expression (expr.left (), name, val),
                    expr.op (),
                    bind_expression (expr.right (), name, val)
                );
            case ExpressionType.POSTFIX:
                return new Expression.postfix (bind_expression (expr.left (), name, val), expr.op ());
            case ExpressionType.FUNCTION:
                return new Expression.function (expr.ident (), bind_expression (expr.right (), name, val));
            default: assert_not_reached ();
        }
    }

    /**
     * Get a copy of an AST in which a variable is replaced by a value.
     */
    public static Ast ast_bind_variable (Ast expression, string name, double val) {
        return new Ast (bind_expression (expression.root (), name, val));
    }

    namespace MathParser {
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
