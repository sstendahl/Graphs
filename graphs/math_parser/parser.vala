// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Parser {
        private Lexer lexer = new Lexer ();

        private static Once<Parser> _instance;

        public static unowned Parser instance () {
            return _instance.once (() => { return new Parser (); });
        }

        public Expression parse (string src, unichar decimal_separator = '.') throws MathError {
            lexer.start_lexing (src, decimal_separator);
            Expression result = expr ();
            lexer.expect_end ();
            return result;
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
            while (true) {
                t = lexer.current_type;
                if (!(t == TokenType.PLUS || t == TokenType.MINUS)) break;
                lexer.next ();

                expr = new BinaryExpression (expr, t, term ());
            }

            return expr;
        }

        private Expression term () throws MathError {
            Expression expr = power ();

            while (true) {
                TokenType t = lexer.current_type;
                // explicit * or /
                if (t == TokenType.STAR || t == TokenType.SLASH) {
                    lexer.next ();
                    /*
                    if (t == TokenType.SLASH && r == 0)
                        throw new MathError.DIV_ZERO ("division by zero");
                    */
                    expr = new BinaryExpression (expr, t, power ());
                    continue;
                }

                // implicit multiplication
                if (t == TokenType.NUMBER || t == TokenType.IDENT || t == TokenType.LPAREN) {
                    expr = new BinaryExpression (expr, TokenType.STAR, power ());
                    continue;
                }
                break;
            }

            return expr;
        }

        private Expression power () throws MathError {
            Expression expr = unary ();

            if (lexer.current_type == TokenType.CARET) {
                lexer.next ();
                expr = new BinaryExpression (expr, TokenType.CARET, power ());
            }

            return expr;
        }

        private Expression unary () throws MathError {
            if (lexer.current_type == TokenType.MINUS) {
                lexer.next ();
                return new UnaryExpression (TokenType.MINUS, postfix ());
            } else if (lexer.current_type == TokenType.PLUS) {
                lexer.next ();
            }

            return postfix ();
        }

        private Expression postfix () throws MathError {
            Expression expr = primary ();

            while (true) {
                if (lexer.current_type == TokenType.FACT) {
                    /*
                    if (v < 0 || v != Math.floor (v))
                        throw new MathError.DOMAIN ("invalid factorial");
                    */
                    expr = new PostfixExpression (expr, TokenType.FACT);
                    lexer.next ();
                    continue;
                }

                if (lexer.current_type == TokenType.SUPERSCRIPT) {
                    var exp = new NumberExpression (lexer.current_val);
                    lexer.next ();
                    expr = new BinaryExpression (expr, TokenType.SUPERSCRIPT, exp);
                    continue;
                }

                break;
            }

            return expr;
        }

        private Expression primary () throws MathError {
            switch (lexer.current_type) {
                case TokenType.NUMBER:
                    var v = new NumberExpression (lexer.current_val);
                    lexer.next ();
                    return v;
                case TokenType.IDENT:
                    Ident id = lexer.current_ident;

                    if (id == Ident.CUSTOM) {
                        string name = lexer.get_current_token_as_string ();
                        lexer.next ();

                        return new VariableExpression (name);
                    }

                    lexer.next ();

                    if (lexer.current_type == TokenType.LPAREN) {
                        lexer.next ();
                        Expression arg = expr ();
                        lexer.expect (TokenType.RPAREN);

                        return new FunctionExpression (id, arg);
                    }

                    switch (id) {
                        case Ident.PI: return new ConstantExpression (Ident.PI);
                        case Ident.E: return new ConstantExpression (Ident.E);
                        case Ident.INF: return new ConstantExpression (Ident.INF);
                        default: throw new MathError.UNKNOWN_FUNCTION ("invalid identifier");
                    }
                case TokenType.LPAREN:
                    lexer.next ();
                    Expression expr = expr ();
                    lexer.expect (TokenType.RPAREN);
                    return expr;
                default:
                    throw new MathError.SYNTAX ("unexpected token");
            }
        }
    }
}
