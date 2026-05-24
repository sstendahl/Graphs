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
        LOG,
        LOG2,
        LOG10,
        SQRT,
        EXP,
        ABS,

        CUSTOM
    }

    public abstract class Expression : Object {}

    public class NumberExpression : Expression {
        public double val;

        public NumberExpression (double v) {
            this.val = v;
        }
    }

    public class ConstantExpression : Expression {
        public Ident constant;

        public ConstantExpression (Ident c) {
            this.constant = c;
        }

        public double val () throws MathError {
            switch (constant) {
                case Ident.PI: return Math.PI;
                case Ident.E: return Math.E;
                case Ident.INF: return double.INFINITY;
                default: throw new MathError.UNKNOWN_FUNCTION ("invalid constant");
            }
        }
    }

    public class VariableExpression : Expression {
        public string name;

        public VariableExpression (string n) {
            this.name = n;
        }
    }

    public class UnaryExpression : Expression {
        public TokenType op;
        public Expression expr;

        public UnaryExpression (TokenType op, Expression e) {
            this.op = op;
            this.expr = e;
        }
    }

    public class BinaryExpression : Expression {
        public TokenType op;
        public Expression left;
        public Expression right;

        public BinaryExpression (Expression l, TokenType op, Expression r) {
            this.left = l;
            this.op = op;
            this.right = r;
        }
    }

    public class FunctionExpression : Expression {
        public Ident ident;
        public Expression arg;

        public FunctionExpression (Ident id, Expression arg) {
            this.ident = id;
            this.arg = arg;
        }
    }

    public class PostfixExpression : Expression {
        public Expression expr;
        public TokenType op;

        public PostfixExpression (Expression e, TokenType op) {
            this.expr = e;
            this.op = op;
        }
    }
}
