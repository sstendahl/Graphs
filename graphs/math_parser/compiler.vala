// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Compiler {
        private Gee.ArrayList<Instruction?> code = new Gee.ArrayList<Instruction?> ();
        private string variable_name;

        private static Once<Compiler> _instance;

        public static unowned Compiler instance () {
            return _instance.once (() => { return new Compiler (); });
        }

        public Instruction[] compile (Expression expr, string variable = "x") throws MathError {
            code.clear ();
            this.variable_name = variable;

            emit (expr);

            Instruction end = Instruction ();
            end.op = OpCode.END;
            end.val = 0.0;

            code.add (end);

            Instruction[] result = new Instruction[code.size];
            for (int i = 0; i < code.size; i++) {
                result[i] = code[i];
            }
            return result;
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

            Instruction i = Instruction ();
            i.op = OpCode.PUSH_X;
            i.val = 0.0;

            code.add (i);
        }

        private void constant (ConstantExpression expr) throws MathError {
            Instruction i = Instruction ();
            i.op = OpCode.PUSH_CONST;
            i.val = expr.val ();

            code.add (i);
        }

        private void number (NumberExpression expr) throws MathError {
            Instruction i = Instruction ();
            i.op = OpCode.PUSH_CONST;
            i.val = expr.val ();

            code.add (i);
        }

        private void unary (UnaryExpression expr) throws MathError {
            emit (expr.expr ());

            Instruction i = Instruction ();

            switch (expr.op ()) {
                case TokenType.MINUS:
                    i.op = OpCode.NEG;
                    break;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid unary operator");
            }

            i.val = 0.0;
            code.add (i);
        }

        private void binary (BinaryExpression expr) throws MathError {
            emit (expr.left ());
            emit (expr.right ());

            Instruction i = Instruction ();

            switch (expr.op ()) {
                case TokenType.PLUS: i.op = OpCode.ADD; break;
                case TokenType.MINUS: i.op = OpCode.SUB; break;
                case TokenType.STAR: i.op = OpCode.MUL; break;
                case TokenType.SLASH: i.op = OpCode.DIV; break;
                case TokenType.CARET: i.op = OpCode.POW; break;
                case TokenType.SUPERSCRIPT: i.op = OpCode.IPOW; break;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid binary operator");
            }

            i.val = 0.0;
            code.add (i);
        }

        private void postfix (PostfixExpression expr) throws MathError {
            emit (expr.expr ());

            Instruction i = Instruction ();

            switch (expr.op ()) {
                case TokenType.FACT: i.op = OpCode.FACT; break;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid postfix operator");
            }

            i.val = 0.0;
            code.add (i);
        }

        private void function (FunctionExpression expr) throws MathError {
            emit (expr.arg ());

            Instruction i = Instruction ();

            switch (expr.ident ()) {
                case Ident.SIN: i.op = OpCode.SIN; break;
                case Ident.COS: i.op = OpCode.COS; break;
                case Ident.TAN: i.op = OpCode.TAN; break;
                case Ident.LOG: i.op = OpCode.LOG; break;
                case Ident.LOG2: i.op = OpCode.LOG2; break;
                case Ident.LOG10: i.op = OpCode.LOG10; break;
                case Ident.SQRT: i.op = OpCode.SQRT; break;
                case Ident.EXP: i.op = OpCode.EXP; break;
                case Ident.ABS: i.op = OpCode.ABS; break;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid function");
            }

            i.val = 0.0;
            code.add (i);
        }
    }
}
