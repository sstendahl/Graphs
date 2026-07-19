// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Compiler {
        private OpCode[] program;
        private int n_ops;
        private double[] data;
        private int n_data;
        private unowned string variable_name;

        private static Once<Compiler> _instance;

        public static unowned Compiler instance () {
            return _instance.once (() => { return new Compiler (); });
        }

        public Program compile (Ast expr, string variable = "x") throws MathError {
            this.program = new OpCode[16];
            this.n_ops = 0;
            this.data = new double[8];
            this.n_data = 0;
            this.variable_name = variable;

            emit (expr.root ());

            /* At this point program may have more memory allocated than we
             * actually use. Since we only ever use this in the array
             * evaluator we do not need to shrink here */
            return new Program ((owned) this.program, (owned) this.data, n_ops);
        }

        private void add_instruction (OpCode op) {
            if (n_ops >= program.length) program.resize (program.length * 2);

            program[n_ops++] = op;
        }

        private void add_constant (double constant) {
            if (n_data >= data.length) data.resize (data.length * 2);

            data[n_data++] = constant;

            add_instruction (OpCode.PUSH_CONST);
        }

        private void emit (Expression expr) throws MathError {
            switch (expr.type ()) {
                case ExpressionType.NUMBER:
                case ExpressionType.CONSTANT:
                    add_constant (expr.val ());
                    return;
                case ExpressionType.VARIABLE: variable (expr); return;
                case ExpressionType.UNARY: unary (expr); return;
                case ExpressionType.BINARY: binary (expr); return;
                case ExpressionType.POSTFIX: postfix (expr); return;
                case ExpressionType.FUNCTION: function (expr); return;
                default: assert_not_reached ();
            }
        }

        private void variable (Expression expr) throws MathError {
            if (expr.name () != variable_name)
                throw new MathError.UNKNOWN_FUNCTION ("invalid variable: " + expr.name ());

            add_instruction (OpCode.PUSH_X);
        }

        private void unary (Expression expr) throws MathError {
            emit (expr.right ());

            switch (expr.op ()) {
                case Operator.SUB: add_instruction (OpCode.NEG); return;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid unary operator");
            }
        }

        private void binary (Expression expr) throws MathError {
            emit (expr.left ());
            emit (expr.right ());

            switch (expr.op ()) {
                case Operator.ADD: add_instruction (OpCode.ADD); return;
                case Operator.SUB: add_instruction (OpCode.SUB); return;
                case Operator.MUL: add_instruction (OpCode.MUL); return;
                case Operator.DIV: add_instruction (OpCode.DIV); return;
                case Operator.POW: add_instruction (OpCode.POW); return;
                case Operator.SUPERSCRIPT: add_instruction (OpCode.IPOW); return;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid binary operator");
            }
        }

        private void postfix (Expression expr) throws MathError {
            emit (expr.left ());

            switch (expr.op ()) {
                case Operator.FACT: add_instruction (OpCode.FACT); return;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid postfix operator");
            }
        }

        private const double DEGREES_TO_RAD = Math.PI / 180;
        private const double RAD_TO_DEGREES = 180 / Math.PI;

        private void to_degrees () {
            add_constant (RAD_TO_DEGREES);
            add_instruction (OpCode.MUL);
        }

        private void to_rad () {
            add_constant (DEGREES_TO_RAD);
            add_instruction (OpCode.MUL);
        }

        private void cot () {
            // cot(x) = 1 / tan(x)
            add_instruction (OpCode.TAN);
            add_instruction (OpCode.INV);
        }

        private void sec () {
            // sec(x) = 1 / cos(x)
            add_instruction (OpCode.COS);
            add_instruction (OpCode.INV);
        }

        private void csc () {
            // csc(x) = 1 / sin(x)
            add_instruction (OpCode.SIN);
            add_instruction (OpCode.INV);
        }

        private void acot () {
            // acot(x) = atan(1 / x)
            add_instruction (OpCode.INV);
            add_instruction (OpCode.ATAN);
        }

        private void asec () {
            // asec(x) = acos(1 / x)
            add_instruction (OpCode.INV);
            add_instruction (OpCode.ACOS);
        }

        private void acsc () {
            // acsc(x) = asin(1 / x)
            add_instruction (OpCode.INV);
            add_instruction (OpCode.ASIN);
        }

        private void function (Expression expr) throws MathError {
            emit (expr.right ());

            switch (expr.ident ()) {
                case Ident.SIN: add_instruction (OpCode.SIN); return;
                case Ident.COS: add_instruction (OpCode.COS); return;
                case Ident.TAN: add_instruction (OpCode.TAN); return;
                case Ident.COT: cot (); return;
                case Ident.SEC: sec (); return;
                case Ident.CSC: csc (); return;

                case Ident.SIND: to_rad (); add_instruction (OpCode.SIN); return;
                case Ident.COSD: to_rad (); add_instruction (OpCode.COS); return;
                case Ident.TAND: to_rad (); add_instruction (OpCode.TAN); return;
                case Ident.COTD: to_rad (); cot (); return;
                case Ident.SECD: to_rad (); sec (); return;
                case Ident.CSCD: to_rad (); csc (); return;

                case Ident.ASIN: add_instruction (OpCode.ASIN); return;
                case Ident.ACOS: add_instruction (OpCode.ACOS); return;
                case Ident.ATAN: add_instruction (OpCode.ATAN); return;
                case Ident.ACOT: acot (); return;
                case Ident.ASEC: asec (); return;
                case Ident.ACSC: acsc (); return;

                case Ident.ASIND: add_instruction (OpCode.ASIN); to_degrees (); return;
                case Ident.ACOSD: add_instruction (OpCode.ACOS); to_degrees (); return;
                case Ident.ATAND: add_instruction (OpCode.ATAN); to_degrees (); return;
                case Ident.ACOTD: acot (); to_degrees (); return;
                case Ident.ASECD: asec (); to_degrees (); return;
                case Ident.ACSCD: acsc (); to_degrees (); return;

                case Ident.LN: add_instruction (OpCode.LN); return;
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
