// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public errordomain MathError {
        SYNTAX,
        UNKNOWN_FUNCTION,
        DOMAIN,
        DIV_ZERO
    }

    private enum TokenType {
        NUMBER,
        OPERATOR,
        IDENT,
        LPAREN,
        RPAREN,
        END
    }

    public enum Operator {
        MUL,
        DIV,
        ADD,
        SUB,
        POW,
        FACT,
        SUPERSCRIPT;

        public int precedence () {
            switch (this) {
                case SUPERSCRIPT: return 0;
                case FACT: return 0;
                case POW: return 0;
                case MUL: return 0;
                case DIV: return 0;
                case ADD: return 1;
                case SUB: return 1;
                default: assert_not_reached ();
            }
        }
    }

    public enum Ident {
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
        LN,
        LOG2,
        LOG10,
        SQRT,
        EXP,
        ABS,

        CUSTOM
    }

    public abstract class Expression {}

    public class NumberExpression : Expression {
        private double _val;

        public NumberExpression (double v) {
            this._val = v;
        }

        public double val () {
            return _val;
        }
    }

    public class ConstantExpression : Expression {
        private Ident _constant;

        public ConstantExpression (Ident c) {
            this._constant = c;
        }

        public Ident constant () {
            return _constant;
        }

        public double val () throws MathError {
            switch (_constant) {
                case Ident.PI: return Math.PI;
                case Ident.E: return Math.E;
                case Ident.INF: return double.INFINITY;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid constant");
            }
        }
    }

    public class VariableExpression : Expression {
        private string _name;

        public VariableExpression (owned string n) {
            this._name = (owned) n;
        }

        public unowned string name () {
            return _name;
        }
    }

    public class UnaryExpression : Expression {
        private Operator _op;
        private Expression _expr;

        public UnaryExpression (Operator op, Expression e) {
            this._op = op;
            this._expr = e;
        }

        public Operator op () {
            return _op;
        }

        public Expression expr () {
            return _expr;
        }
    }

    public class BinaryExpression : Expression {
        private Operator _op;
        private Expression _left;
        private Expression _right;

        public BinaryExpression (Expression l, Operator op, Expression r) {
            this._left = l;
            this._op = op;
            this._right = r;
        }

        public Operator op () {
            return _op;
        }

        public Expression left () {
            return _left;
        }

        public Expression right () {
            return _right;
        }
    }

    public class FunctionExpression : Expression {
        private Ident _ident;
        private Expression _arg;

        public FunctionExpression (Ident id, Expression arg) {
            this._ident = id;
            this._arg = arg;
        }

        public Ident ident () {
            return _ident;
        }

        public Expression arg () {
            return _arg;
        }
    }

    public class PostfixExpression : Expression {
        private Expression _expr;
        private Operator _op;

        public PostfixExpression (Expression e, Operator op) {
            this._expr = e;
            this._op = op;
        }

        public Expression expr () {
            return _expr;
        }

        public Operator op () {
            return _op;
        }
    }

    public enum OpCode {
        // control
        PUSH_CONST,
        PUSH_X,

        // basic operands
        ADD,
        SUB,
        MUL,
        DIV,
        POW,
        IPOW,

        // pre and postfix
        NEG,
        INV,
        FACT,

        // trig
        SIN,
        COS,
        TAN,
        ASIN,
        ACOS,
        ATAN,

        // misc
        LN,
        LOG2,
        LOG10,
        SQRT,
        EXP,
        ABS
    }

    [Compact (opaque = true)]
    public class Program {
        private OpCode[] _program;
        private double[] _data;
        private int _plen;

        public Program (owned OpCode[] program, owned double[] data, int plen) {
            this._program = (owned) program;
            this._data = (owned) data;
            this._plen = plen;
        }

        public double[] eval (double[] input) {
            double[] output = new double[input.length];
            MathParser.eval_array (_program, _data, _plen, input, output, input.length);
            return output;
        }
    }
}
