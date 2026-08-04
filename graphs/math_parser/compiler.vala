// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    [Compact (opaque = true)]
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

        public Program compile (Ast expr, string variable) throws MathError {
            this.program = new OpCode[16];
            this.n_ops = 0;
            this.data = new double[8];
            this.n_data = 0;
            this.variable_name = variable;

            if (!emit (expr.root ())) {
                throw new MathError.UNKNOWN_FUNCTION ("invalid variable: " + variable_name);
            }

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

        private bool emit (Expression expr) {
            switch (expr.type ()) {
                case ExpressionType.NUMBER:
                case ExpressionType.CONSTANT:
                    add_constant (expr.val ());
                    return true;
                case ExpressionType.VARIABLE: return variable (expr);
                case ExpressionType.UNARY: return unary (expr);
                case ExpressionType.BINARY: return binary (expr);
                case ExpressionType.POSTFIX: return postfix (expr);
                case ExpressionType.FUNCTION: return function (expr);
                default: assert_not_reached ();
            }
        }

        private bool variable (Expression expr) {
            if (expr.name () != variable_name) {
                // We can safely override the variable_name here as we no longer
                // need to check it as is this the error path.
                this.variable_name = expr.name ();
                return false;
            }

            add_instruction (OpCode.PUSH_X);
            return true;
        }

        private bool unary (Expression expr) {
            if (!emit (expr.right ())) return false;

            switch (expr.op ()) {
                case Operator.SUB: add_instruction (OpCode.NEG); return true;
                default: assert_not_reached ();
            }
        }

        private bool binary (Expression expr) {
            if (!emit (expr.left ())) return false;
            if (!emit (expr.right ())) return false;

            switch (expr.op ()) {
                case Operator.ADD: add_instruction (OpCode.ADD); return true;
                case Operator.SUB: add_instruction (OpCode.SUB); return true;
                case Operator.MUL: add_instruction (OpCode.MUL); return true;
                case Operator.DIV: add_instruction (OpCode.DIV); return true;
                case Operator.POW: add_instruction (OpCode.POW); return true;
                case Operator.SUPERSCRIPT: add_instruction (OpCode.IPOW); return true;
                default: assert_not_reached ();
            }
        }

        private bool postfix (Expression expr) {
            if (!emit (expr.left ())) return false;

            switch (expr.op ()) {
                case Operator.FACT: add_instruction (OpCode.FACT); return true;
                default: assert_not_reached ();
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

        private bool function (Expression expr) {
            if (!emit (expr.right ())) return false;

            switch (expr.ident ()) {
                case Ident.SIN: add_instruction (OpCode.SIN); return true;
                case Ident.COS: add_instruction (OpCode.COS); return true;
                case Ident.TAN: add_instruction (OpCode.TAN); return true;
                case Ident.COT: cot (); return true;
                case Ident.SEC: sec (); return true;
                case Ident.CSC: csc (); return true;

                case Ident.SIND: to_rad (); add_instruction (OpCode.SIN); return true;
                case Ident.COSD: to_rad (); add_instruction (OpCode.COS); return true;
                case Ident.TAND: to_rad (); add_instruction (OpCode.TAN); return true;
                case Ident.COTD: to_rad (); cot (); return true;
                case Ident.SECD: to_rad (); sec (); return true;
                case Ident.CSCD: to_rad (); csc (); return true;

                case Ident.ASIN: add_instruction (OpCode.ASIN); return true;
                case Ident.ACOS: add_instruction (OpCode.ACOS); return true;
                case Ident.ATAN: add_instruction (OpCode.ATAN); return true;
                case Ident.ACOT: acot (); return true;
                case Ident.ASEC: asec (); return true;
                case Ident.ACSC: acsc (); return true;

                case Ident.ASIND: add_instruction (OpCode.ASIN); to_degrees (); return true;
                case Ident.ACOSD: add_instruction (OpCode.ACOS); to_degrees (); return true;
                case Ident.ATAND: add_instruction (OpCode.ATAN); to_degrees (); return true;
                case Ident.ACOTD: acot (); to_degrees (); return true;
                case Ident.ASECD: asec (); to_degrees (); return true;
                case Ident.ACSCD: acsc (); to_degrees (); return true;

                case Ident.LN: add_instruction (OpCode.LN); return true;
                case Ident.LOG2: add_instruction (OpCode.LOG2); return true;
                case Ident.LOG10: add_instruction (OpCode.LOG10); return true;
                case Ident.SQRT: add_instruction (OpCode.SQRT); return true;
                case Ident.EXP: add_instruction (OpCode.EXP); return true;
                case Ident.ABS: add_instruction (OpCode.ABS); return true;
                default: assert_not_reached ();
            }
        }
    }
}
