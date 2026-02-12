// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Preprocessor {
        private Lexer lexer = new Lexer (true);
        private StringBuilder builder;

        private static Once<Preprocessor> _instance;

        public static unowned Preprocessor instance () {
            return _instance.once (() => { return new Preprocessor (); });
        }

        public string preprocess (string src) throws MathError {
            this.builder = new StringBuilder ();
            lexer.start_lexing (src);
            expr ();
            lexer.expect_end ();
            return builder.free_and_steal ();
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

        private void expr () throws MathError {
            term ();
            TokenType t;
            while (true) {
                t = lexer.current_type;
                if (!(t == TokenType.PLUS || t == TokenType.MINUS)) break;
                builder.append_c ((t == TokenType.PLUS) ? '+' : '-');
                lexer.next ();
                term ();
            }
        }

        private void term () throws MathError {
            power ();

            while (true) {
                TokenType t = lexer.current_type;
                // explicit * or /
                if (t == TokenType.STAR || t == TokenType.SLASH) {
                    builder.append_c ((t == TokenType.STAR) ? '*' : '/');
                    lexer.next ();
                    power ();
                    continue;
                }

                // implicit multiplication
                if (t == TokenType.NUMBER || t == TokenType.IDENT || t == TokenType.LPAREN) {
                    builder.append_c ('*');
                    power ();
                    continue;
                }
                break;
            }
        }

        private void power () throws MathError {
            unary ();
            if (lexer.current_type == TokenType.CARET) {
                builder.append_c ('^');
                lexer.next ();
            }
        }

        private void unary () throws MathError {
            if (lexer.current_type == TokenType.MINUS) {
                builder.append_c ('-');
                lexer.next ();
                unary ();
                return;
            }
            postfix ();
        }

        private void postfix () throws MathError {
            double? v = primary ();

            bool output = false;
            while (true) {
                if (lexer.current_type == TokenType.FACT) {
                    if (v != null) {
                        if (v < 0 || v != Math.floor (v))
                            throw new MathError.DOMAIN ("invalid factorial");
                        v = factorial ((int) v);
                        builder.append (v.to_string ());
                    } else {
                        builder.append_c ('!');
                    }

                    output = true;
                    lexer.next ();
                    continue;
                }

                if (lexer.current_type == TokenType.SUPERSCRIPT) {
                    int exp = (int) lexer.current_val;
                    if (v != null) {
                        lexer.next ();
                        v = ipow (v, exp);
                        builder.append (v.to_string ());
                    } else {
                        builder.append ("**");
                        builder.append (exp.to_string ());
                    }
                    output = true;
                    continue;
                }

                break;
            }

            if (!output && v != null) builder.append (v.to_string ());
        }

        private double? primary () throws MathError {
            switch (lexer.current_type) {
                case TokenType.NUMBER:
                    double v = lexer.current_val;
                    lexer.next ();
                    return v;
                case TokenType.IDENT:
                    Ident id = lexer.current_ident;
                    if (id == Ident.CUSTOM) {
                        builder.append (lexer.get_current_token_as_string ().down ());
                        lexer.next ();
                        return null;
                    }

                    lexer.next ();
                    switch (id) {
                        case Ident.PI: return Math.PI;
                        case Ident.E: return Math.E;
                        default: break;
                    }

                    lexer.expect (TokenType.LPAREN);
                    function_pre (id);
                    expr ();
                    lexer.expect (TokenType.RPAREN);
                    function_post (id);

                    return null;
                case TokenType.LPAREN:
                    builder.append_c ('(');
                    lexer.next ();
                    expr ();
                    lexer.expect (TokenType.RPAREN);
                    builder.append_c (')');
                    return null;
                default:
                    throw new MathError.SYNTAX ("unexpected token");
            }
        }

        private void function_pre (Ident id) {
            switch (id) {
                // trig radians
                case Ident.SIN: builder.append ("sin("); break;
                case Ident.COS: builder.append ("cos("); break;
                case Ident.TAN: builder.append ("tan("); break;
                case Ident.COT: builder.append ("1/tan("); break;
                case Ident.SEC: builder.append ("1/cos("); break;
                case Ident.CSC: builder.append ("1/sin("); break;

                // trig degrees
                case Ident.SIND: builder.append ("sin(0.017453292519943295*("); break;
                case Ident.COSD: builder.append ("cos(0.017453292519943295*("); break;
                case Ident.TAND: builder.append ("tan(0.017453292519943295*("); break;
                case Ident.COTD: builder.append ("1/tan(0.017453292519943295*("); break;
                case Ident.SECD: builder.append ("1/cos(0.017453292519943295*("); break;
                case Ident.CSCD: builder.append ("1/sin(0.017453292519943295*("); break;

                // inverse trig radians
                case Ident.ASIN: builder.append ("arcsin("); break;
                case Ident.ACOS: builder.append ("arccos("); break;
                case Ident.ATAN: builder.append ("arctan("); break;
                case Ident.ACOT: builder.append ("arcsin(1/sqrt(1+"); break;
                case Ident.ASEC: builder.append ("arccos(1/("); break;
                case Ident.ACSC: builder.append ("arcsin(1/("); break;

                // inverse trig degrees
                case Ident.ASIND: builder.append ("57.29577951308232*arcsin("); break;
                case Ident.ACOSD: builder.append ("57.29577951308232*arccos("); break;
                case Ident.ATAND: builder.append ("57.29577951308232*arctan("); break;
                case Ident.ACOTD: builder.append ("57.29577951308232*arcsin(1/sqrt(1+"); break;
                case Ident.ASECD: builder.append ("57.29577951308232*arccos(1/("); break;
                case Ident.ACSCD: builder.append ("57.29577951308232*arcsin(1/("); break;

                // misc
                case Ident.LOG: builder.append ("log("); break;
                case Ident.LOG2: builder.append ("log2("); break;
                case Ident.LOG10: builder.append ("log10("); break;
                case Ident.SQRT: builder.append ("sqrt("); break;
                case Ident.EXP: builder.append ("exp("); break;
                case Ident.ABS: builder.append ("abs("); break;

                default: assert_not_reached ();
            }
        }

        private void function_post (Ident id) {
            switch (id) {
                case Ident.ACOT: case Ident.ACOTD: builder.append ("**2))"); break;
                case Ident.SIND: case Ident.COSD: case Ident.TAND:
                case Ident.COTD: case Ident.SEC: case Ident.CSC:
                case Ident.ASEC: case Ident.ACSC:
                case Ident.ASECD: case Ident.ACSCD:
                    builder.append ("))"); break;
                default: builder.append_c (')'); break;
            }
        }
    }
}
