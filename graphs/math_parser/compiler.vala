// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Compiler {
        private OpCode[] program;
        private int n_ops;
        private double[] data;
        private int n_data;
        private string variable_name;

        private static Once<Compiler> _instance;

        public static unowned Compiler instance () {
            return _instance.once (() => { return new Compiler (); });
        }

        public OpCode[] compile (Expression expr, out double[] data, string variable = "x") throws MathError {
            this.program = new OpCode[16];
            this.n_ops = 0;
            this.data = new double[8];
            this.n_data = 0;
            this.variable_name = variable;

            emit (expr);

            add_instruction (OpCode.END);

            program.resize (n_ops);
            data.resize (n_data);

            data = (owned) this.data;
            return (owned) program;
        }

        private void add_instruction (OpCode op) {
            if (n_ops >= program.length) program.resize (program.length * 2);

            program[n_ops++] = op;
        }

        private void add_constant (double constant) {
            if (n_data >= data.length) data.resize (data.length * 2);

            data[n_data++] = constant;
        }

        private void emit (Expression expr) throws MathError {
            if (expr is NumberExpression) { number ((NumberExpression) expr); return; }
            if (expr is ConstantExpression) { constant ((ConstantExpression) expr); return; }
            if (expr is VariableExpression) { variable ((VariableExpression) expr); return; }
            if (expr is UnaryExpression) { unary ((UnaryExpression) expr); return; }
            if (expr is BinaryExpression) { binary ((BinaryExpression) expr); return; }
            if (expr is FunctionExpression) { function ((FunctionExpression) expr); return; }
            if (expr is PostfixExpression) { postfix ((PostfixExpression) expr); return; }

            assert_not_reached ();
        }

        private void variable (VariableExpression expr) throws MathError {
            if (expr.name () != variable_name)
                throw new MathError.UNKNOWN_FUNCTION ("invalid variable: " + expr.name ());

            add_instruction (OpCode.PUSH_X);
        }

        private void constant (ConstantExpression expr) throws MathError {
            add_instruction (OpCode.PUSH_CONST);
            add_constant (expr.val ());
        }

        private void number (NumberExpression expr) throws MathError {
            add_instruction (OpCode.PUSH_CONST);
            add_constant (expr.val ());
        }

        private void unary (UnaryExpression expr) throws MathError {
            emit (expr.expr ());

            switch (expr.op ()) {
                case TokenType.MINUS: add_instruction (OpCode.NEG); return;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid unary operator");
            }
        }

        private void binary (BinaryExpression expr) throws MathError {
            emit (expr.left ());
            emit (expr.right ());

            switch (expr.op ()) {
                case TokenType.PLUS: add_instruction (OpCode.ADD); return;
                case TokenType.MINUS: add_instruction (OpCode.SUB); return;
                case TokenType.STAR: add_instruction (OpCode.MUL); return;
                case TokenType.SLASH: add_instruction (OpCode.DIV); return;
                case TokenType.CARET: add_instruction (OpCode.POW); return;
                case TokenType.SUPERSCRIPT: add_instruction (OpCode.IPOW); return;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid binary operator");
            }
        }

        private void postfix (PostfixExpression expr) throws MathError {
            emit (expr.expr ());

            switch (expr.op ()) {
                case TokenType.FACT: add_instruction (OpCode.FACT); return;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid postfix operator");
            }
        }

        private void function (FunctionExpression expr) throws MathError {
            emit (expr.arg ());

            switch (expr.ident ()) {
                case Ident.SIN: add_instruction (OpCode.SIN); return;
                case Ident.COS: add_instruction (OpCode.COS); return;
                case Ident.TAN: add_instruction (OpCode.TAN); return;
                case Ident.LOG: add_instruction (OpCode.LOG); return;
                case Ident.LOG2: add_instruction (OpCode.LOG2); return;
                case Ident.LOG10: add_instruction (OpCode.LOG10); return;
                case Ident.SQRT: add_instruction (OpCode.SQRT); return;
                case Ident.EXP: add_instruction (OpCode.EXP); return;
                case Ident.ABS: add_instruction (OpCode.ABS); return;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid function");
            }
        }
    }
}
