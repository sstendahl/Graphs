// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public errordomain MathError {
        SYNTAX,
        UNKNOWN_FUNCTION,
        DOMAIN,
        DIV_ZERO
    }

    public enum TokenType {
        NUMBER,
        IDENT,
        PLUS, MINUS, STAR, SLASH,
        CARET,
        FACT,
        SUPERSCRIPT,
        LPAREN, RPAREN,
        END
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

        public VariableExpression (string n) {
            this._name = n;
        }

        public string name () {
            return _name;
        }
    }

    public class UnaryExpression : Expression {
        private TokenType _op;
        private Expression _expr;

        public UnaryExpression (TokenType op, Expression e) {
            this._op = op;
            this._expr = e;
        }

        public TokenType op () {
            return _op;
        }

        public Expression expr () {
            return _expr;
        }
    }

    public class BinaryExpression : Expression {
        private TokenType _op;
        private Expression _left;
        private Expression _right;

        public BinaryExpression (Expression l, TokenType op, Expression r) {
            this._left = l;
            this._op = op;
            this._right = r;
        }

        public TokenType op () {
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
        private TokenType _op;

        public PostfixExpression (Expression e, TokenType op) {
            this._expr = e;
            this._op = op;
        }

        public Expression expr () {
            return _expr;
        }

        public TokenType op () {
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
}
