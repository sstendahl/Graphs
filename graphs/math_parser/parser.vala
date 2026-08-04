// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    [Compact (opaque = true)]
    private class Parser {
        private Lexer lexer = new Lexer ();

        private static Once<Parser> _instance;

        public static unowned Parser instance () {
            return _instance.once (() => { return new Parser (); });
        }

        public Ast parse (string src, unichar decimal_separator = '.') throws MathError {
            lexer.start_lexing (src, decimal_separator);
            Expression result = expr ();
            if (lexer.current_type != TokenType.END)
                throw new MathError.SYNTAX ("trailing input");
            return new Ast ((owned) result);
        }

        /* Grammar:
           expr    -> term ((+|-) term)*
           term    -> power ((*|/) power)*
           term    -> power expr
           power   -> unary ((^|**) power)?
           unary   -> (- unary) | postfix
           postfix -> primary (!)*
           primary -> number | constant | func | '(' expr ')'
        */

        private Expression expr () throws MathError {
            Expression expr = term ();

            TokenType t;
            Operator op;
            while (true) {
                t = lexer.current_type;
                if (t != TokenType.OPERATOR) break;
                op = lexer.current_op;
                if (!(op == Operator.ADD || op == Operator.SUB)) break;
                lexer.next ();

                expr = new Expression.binary ((owned) expr, op, term ());
            }

            return (owned) expr;
        }

        private Expression term () throws MathError {
            Expression expr = power ();

            TokenType t;
            Operator op;
            while (true) {
                t = lexer.current_type;

                // implicit multiplication
                if (t == TokenType.NUMBER || t == TokenType.IDENT || t == TokenType.LPAREN) {
                    expr = new Expression.binary ((owned) expr, Operator.MUL, power ());
                    continue;
                }

                if (t != TokenType.OPERATOR) break;

                op = lexer.current_op;

                // explicit * or /
                if (op == Operator.MUL || op == Operator.DIV) {
                    lexer.next ();
                    expr = new Expression.binary ((owned) expr, op, power ());
                    continue;
                }
                break;
            }

            return expr;
        }

        private Expression power () throws MathError {
            Expression expr = unary ();

            if (lexer.current_type == TokenType.OPERATOR && lexer.current_op == Operator.POW) {
                lexer.next ();
                expr = new Expression.binary ((owned) expr, Operator.POW, power ());
            }

            return expr;
        }

        private Expression? unary () throws MathError {
            if (lexer.current_type == TokenType.OPERATOR) {
                if (lexer.current_op == Operator.SUB) {
                    lexer.next ();
                    return new Expression.unary (Operator.SUB, postfix ());
                } else if (lexer.current_op == Operator.ADD) {
                    lexer.next ();
                }
            }

            return postfix ();
        }

        private Expression? postfix () throws MathError {
            Expression expr = primary ();

            while (true) {
                if (lexer.current_type != TokenType.OPERATOR) break;

                if (lexer.current_op == Operator.FACT) {
                    expr = new Expression.postfix ((owned) expr, Operator.FACT);
                    lexer.next ();
                    continue;
                }

                if (lexer.current_op == Operator.SUPERSCRIPT) {
                    var exp = new Expression.number (lexer.current_val);
                    lexer.next ();
                    expr = new Expression.binary ((owned) expr, Operator.SUPERSCRIPT, (owned) exp);
                    continue;
                }

                break;
            }

            return expr;
        }

        private Expression? primary () throws MathError {
            switch (lexer.current_type) {
                case TokenType.NUMBER:
                    var v = new Expression.number (lexer.current_val);
                    lexer.next ();
                    return v;
                case TokenType.IDENT:
                    Ident id = lexer.current_ident;

                    if (id == Ident.CUSTOM) {
                        string name = lexer.get_current_token_as_string ();
                        lexer.next ();

                        return new Expression.variable ((owned) name);
                    }

                    lexer.next ();

                    if (lexer.current_type == TokenType.LPAREN) {
                        lexer.next ();
                        Expression arg = expr ();
                        if (lexer.current_type != TokenType.RPAREN)
                            throw new MathError.SYNTAX ("expected token");
                        lexer.next ();

                        return new Expression.function (id, (owned) arg);
                    }

                    switch (id) {
                        case Ident.PI: return new Expression.constant (Ident.PI);
                        case Ident.E: return new Expression.constant (Ident.E);
                        case Ident.INF: return new Expression.constant (Ident.INF);
                        default: assert_not_reached ();
                    }
                case TokenType.LPAREN:
                    lexer.next ();
                    Expression expr = expr ();
                    if (lexer.current_type != TokenType.RPAREN)
                        throw new MathError.SYNTAX ("expected token");
                    lexer.next ();
                    return expr;
                default:
                    throw new MathError.SYNTAX ("unexpected token");
            }
        }
    }
}
