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

    public enum ExpressionType {
        NUMBER,
        CONSTANT,
        VARIABLE,
        UNARY,
        BINARY,
        POSTFIX,
        FUNCTION;
    }

    [Compact (opaque = true)]
    public class Expression {
        private ExpressionType _type;

        private Expression _left;
        private Expression _right;

        // This value will either be an Ident or an Operator, but as we only
        // need one at a time, save space reserving just a single uint.
        private uint _enum;
        private double _val;
        private string _name;

        public Expression.number (double v) {
            this._type = ExpressionType.NUMBER;
            this._val = v;
        }

        public Expression.constant (Ident c) {
            this._type = ExpressionType.CONSTANT;
            this._enum = c;
        }

        public Expression.variable (owned string n) {
            this._type = ExpressionType.VARIABLE;
            this._name = (owned) n;
        }

        public Expression.unary (Operator op, owned Expression e) {
            this._type = ExpressionType.UNARY;
            this._enum = op;
            this._right = (owned) e;
        }

        public Expression.binary (owned Expression l, Operator op, owned Expression r) {
            this._type = ExpressionType.BINARY;
            this._left = (owned) l;
            this._enum = op;
            this._right = (owned) r;
        }

        public Expression.postfix (owned Expression e, Operator op) {
            this._type = ExpressionType.POSTFIX;
            this._left = (owned) e;
            this._enum = op;
        }

        public Expression.function (Ident id, owned Expression arg) {
            this._type = ExpressionType.FUNCTION;
            this._enum = id;
            this._right = (owned) arg;
        }

        public ExpressionType type () {
            return _type;
        }

        public unowned Expression left () {
            return _left;
        }

        public unowned Expression right () {
            return _right;
        }

        public double val () throws MathError {
            if (_type == ExpressionType.NUMBER) return _val;

            switch ((Ident) _enum) {
                case Ident.PI: return Math.PI;
                case Ident.E: return Math.E;
                case Ident.INF: return double.INFINITY;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid constant");
            }
        }

        public unowned string name () {
            return _name;
        }

        public Operator op () {
            return (Operator) _enum;
        }

        public Ident ident () {
            return (Ident) _enum;
        }
    }

    public class Ast {
        private Expression _root;

        public Ast (owned Expression root) {
            this._root = (owned) root;
        }

        public unowned Expression root () {
            return _root;
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
