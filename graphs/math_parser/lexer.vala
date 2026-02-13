// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class Lexer {
        private unowned string src;
        private unichar c;
        private unichar decimal_separator;
        private bool allow_custom_ident;

        public TokenType current_type;
        public Ident current_ident;
        public double current_val;

        private int current_start;
        private int current_end;

        public Lexer (bool allow_custom_ident = false) {
            this.allow_custom_ident = allow_custom_ident;
        }

        public void start_lexing (string src, unichar decimal_separator = '.') throws MathError {
            this.src = src;
            this.current_end = 0;
            this.decimal_separator = decimal_separator;
            next ();
        }

        public void next () throws MathError {
            current_start = current_end;
            while (true) {
                if (!src.get_next_char (ref current_end, out c)) {
                    if (current_end == 0) throw new MathError.SYNTAX ("empty expression");
                    current_type = TokenType.END;
                    return;
                }
                if (!c.isspace ()) break;
            }

            // Number
            if (c.isdigit () || c == decimal_separator) {
                handle_number ();
                return;
            }

            // Identifier
            if (c.isalpha () || c == 'π') {
                handle_identifier ();
                return;
            }

            if (c == '*') {
                // look ahead and treat double asterisk as caret
                int tmp_idx = current_end;
                if (!src.get_next_char (ref tmp_idx, out c))
                    throw new MathError.SYNTAX ("expected token");
                if (c == '*') {
                    current_type = TokenType.CARET;
                    current_end = tmp_idx;
                } else current_type = TokenType.STAR;
                return;
            }

            // Single-character token
            switch (c) {
                case '+': current_type = TokenType.PLUS; break;
                case '-': current_type = TokenType.MINUS; break;
                case '/': current_type = TokenType.SLASH; break;
                case '^': current_type = TokenType.CARET; break;
                case '!': current_type = TokenType.FACT; break;
                case '(': current_type = TokenType.LPAREN; break;
                case ')': current_type = TokenType.RPAREN; break;
                // Superscript
                case '⁰': current_type = TokenType.SUPERSCRIPT; current_val = 0; break;
                case '¹': current_type = TokenType.SUPERSCRIPT; current_val = 1; break;
                case '²': current_type = TokenType.SUPERSCRIPT; current_val = 2; break;
                case '³': current_type = TokenType.SUPERSCRIPT; current_val = 3; break;
                case '⁴': current_type = TokenType.SUPERSCRIPT; current_val = 4; break;
                case '⁵': current_type = TokenType.SUPERSCRIPT; current_val = 5; break;
                case '⁶': current_type = TokenType.SUPERSCRIPT; current_val = 6; break;
                case '⁷': current_type = TokenType.SUPERSCRIPT; current_val = 7; break;
                case '⁸': current_type = TokenType.SUPERSCRIPT; current_val = 8; break;
                case '⁹': current_type = TokenType.SUPERSCRIPT; current_val = 9; break;
                default: throw new MathError.SYNTAX ("invalid token");
            }
        }

        private void handle_number () throws MathError {
            bool seen_dot = false;
            bool last_is_dot = false;
            bool seen_exp = false;
            int idx = current_end;
            int tmp_idx = idx;

            long int_part = 0;
            long frac_part = 0;
            int frac_digits = 0;
            int exp = 0;
            int exp_sign = 1;

            int digit;

            while (true) {
                digit = c.digit_value ();
                if (digit >= 0) {
                    if (seen_exp) {
                        exp = exp * 10 + digit;
                    } else if (seen_dot) {
                        frac_part = frac_part * 10 + digit;
                        frac_digits++;
                    } else {
                        int_part = int_part * 10 + digit;
                    }

                    last_is_dot = false;
                } else if (c == decimal_separator) {
                    if (seen_dot || seen_exp)
                        throw new MathError.SYNTAX ("invalid number");
                    seen_dot = true;
                    last_is_dot = true;
                } else if ((c == 'e' || c == 'E') && !seen_exp) {
                    // Look ahead to see if this is really an exponent
                    if (!src.get_next_char (ref tmp_idx, out c)) break;

                    // Optional sign
                    if (c == '+' || c == '-') {
                        if (c == '-') exp_sign = -1;
                        if (!src.get_next_char (ref tmp_idx, out c)) break;
                    }

                    // Must have at least one digit to be an exponent
                    if (!c.isdigit ()) break;
                    seen_exp = true;
                    last_is_dot = false;
                    idx = tmp_idx;
                    continue;
                } else if (!(c == '.' || c == ',' || c.isspace ())) break;

                // advance to next character
                idx = tmp_idx;
                if (!src.get_next_char (ref tmp_idx, out c)) break;
            }

            // must contain at least one digit and must not have a trailing dot
            if (last_is_dot) throw new MathError.SYNTAX ("invalid number");

            double val = int_part;
            if (seen_dot) val += frac_part / ipow (10d, frac_digits);
            if (seen_exp && exp != 0) {
                int e = exp_sign * exp;
                val *= (e > 0 && e <= 308) ? ipow (10d, e) : Math.pow (10d, e);
            }

            current_type = TokenType.NUMBER;
            current_val = val;
            current_end = idx;
        }

        private inline void fail_identifier (ref int state) throws MathError {
            if (!allow_custom_ident || !c.isalpha ())
                throw new MathError.UNKNOWN_FUNCTION ("invalid identifier");
            current_ident = Ident.CUSTOM;
            state = 200;
        }

        private void handle_identifier () throws MathError {
            current_type = TokenType.IDENT;
            current_ident = Ident.CUSTOM;

            int state = 0;
            int tmp_idx = current_end;

            c = c.tolower ();
            while (true) {
                // process current char in trie
                switch (state) {
                    case 0:
                        switch (c) {
                            case 'π': {
                                current_ident = Ident.PI;
                                state = 200;
                                break;
                            }
                            case 'p': state = 1; break;
                            case 'e': state = 10; break;
                            case 's': state = 20; break;
                            case 'c': state = 40; break;
                            case 't': state = 60; break;
                            case 'l': state = 70; break;
                            case 'a': state = 80; break;
                            default: fail_identifier (ref state); break;
                        }
                        break;

                    // p
                    case 1:
                        if (c == 'i') { current_ident = Ident.PI; state = 200; }
                        else fail_identifier (ref state); break;

                    // e
                    case 10:
                        if (c == 'x') state = 11;
                        else fail_identifier (ref state); break;

                    // ex
                    case 11:
                        if (c == 'p') { current_ident = Ident.EXP; state = 200; }
                        else fail_identifier (ref state); break;

                    // s
                    case 20:
                        if (c == 'i') state = 21;
                        else if (c == 'e') state = 25;
                        else if (c == 'q') state = 28;
                        else fail_identifier (ref state); break;

                    // si
                    case 21:
                        if (c == 'n') { current_ident = Ident.SIN; state = 22; }
                        else fail_identifier (ref state); break;

                    // sin
                    case 22:
                        if (c == 'd') { current_ident = Ident.SIND; state = 200; }
                        else fail_identifier (ref state); break;

                    // se
                    case 25:
                        if (c == 'c') { current_ident = Ident.SEC; state = 26; }
                        else fail_identifier (ref state); break;

                    // sec
                    case 26:
                        if (c == 'd') { current_ident = Ident.SECD; state = 200; }
                        else fail_identifier (ref state); break;

                    // sq
                    case 28:
                        if (c == 'r') state = 29;
                        else fail_identifier (ref state); break;

                    // sqr
                    case 29:
                        if (c == 't') { current_ident = Ident.SQRT; state = 200; }
                        else fail_identifier (ref state); break;

                    // c
                    case 40:
                        if (c == 'o') state = 41;
                        else if (c == 's') state = 45;
                        else fail_identifier (ref state); break;

                    // co
                    case 41:
                        if (c == 's') { current_ident = Ident.COS; state = 42; }
                        else if (c == 't') { current_ident = Ident.COT; state = 43; }
                        else fail_identifier (ref state); break;

                    // cos
                    case 42:
                        if (c == 'd') { current_ident = Ident.COSD; state = 200; }
                        else fail_identifier (ref state); break;

                    // cot
                    case 43:
                        if (c == 'd') { current_ident = Ident.COTD; state = 200; }
                        else fail_identifier (ref state); break;

                    // cs
                    case 45:
                        if (c == 'c') { current_ident = Ident.CSC; state = 46; }
                        else fail_identifier (ref state); break;

                    // csc
                    case 46:
                        if (c == 'd') { current_ident = Ident.CSCD; state = 200; }
                        else fail_identifier (ref state); break;

                    // t
                    case 60:
                        if (c == 'a') state = 61;
                        else fail_identifier (ref state); break;

                    // ta
                    case 61:
                        if (c == 'n') { current_ident = Ident.TAN; state = 62; }
                        else fail_identifier (ref state); break;

                    // tan
                    case 62:
                        if (c == 'd') { current_ident = Ident.TAND; state = 200; }
                        else fail_identifier (ref state); break;

                    // l
                    case 70:
                        if (c == 'o') state = 71;
                        else fail_identifier (ref state); break;

                    // lo
                    case 71:
                        if (c == 'g') { current_ident = Ident.LOG; state = 72; }
                        else fail_identifier (ref state); break;

                    // log
                    case 72:
                        if (c == '2') { current_ident = Ident.LOG2; state = 200; }
                        else if (c == '1') { current_ident = Ident.CUSTOM; state = 73; }
                        else fail_identifier (ref state); break;

                    // log1
                    case 73:
                        if (c == '0') { current_ident = Ident.LOG10; state = 200; }
                        else fail_identifier (ref state); break;

                    // a
                    case 80:
                        if (c == 'b') state = 81;
                        else if (c == 'r') state = 83;
                        else if (c == 'c') state = 90;
                        else if (c == 's') state = 96;
                        else if (c == 't') state = 101;
                        else fail_identifier (ref state); break;

                    // ab
                    case 81:
                        if (c == 's') { current_ident = Ident.ABS; state = 200; }
                        else fail_identifier (ref state); break;

                    // ar
                    case 83:
                        if (c == 'c') state = 84;
                        else fail_identifier (ref state); break;

                    // arc
                    case 84:
                        if (c == 'c') state = 90;
                        else if (c == 's') state = 96;
                        else if (c == 't') state = 101;
                        else fail_identifier (ref state); break;

                    // a(rc)c
                    case 90:
                        if (c == 'o') state = 91;
                        else if (c == 's') state = 94;
                        else fail_identifier (ref state); break;

                    // a(rc)co
                    case 91:
                        if (c == 's') { current_ident = Ident.ACOS; state = 92; }
                        else if (c == 't') { current_ident = Ident.ACOT; state = 93; }
                        else fail_identifier (ref state); break;

                    // a(rc)cos
                    case 92:
                        if (c == 'd') { current_ident = Ident.ACOSD; state = 200; }
                        else fail_identifier (ref state); break;

                    // a(rc)cot
                    case 93:
                        if (c == 'd') { current_ident = Ident.ACOTD; state = 200; }
                        else fail_identifier (ref state); break;

                    // a(rc)cs
                    case 94:
                        if (c == 'c') { current_ident = Ident.ACSC; state = 95; }
                        else fail_identifier (ref state); break;

                    // a(rc)csc
                    case 95:
                        if (c == 'd') { current_ident = Ident.ACSCD; state = 200; }
                        else fail_identifier (ref state); break;

                    // a(rc)s
                    case 96:
                        if (c == 'e') state = 97;
                        else if (c == 'i') state = 99;
                        else fail_identifier (ref state); break;

                    // a(rc)se
                    case 97:
                        if (c == 'c') { current_ident = Ident.ASEC; state = 98; }
                        else fail_identifier (ref state); break;

                    // a(rc)sec
                    case 98:
                        if (c == 'd') { current_ident = Ident.ASECD; state = 200; }
                        else fail_identifier (ref state); break;

                    // a(rc)si
                    case 99:
                        if (c == 'n') { current_ident = Ident.ASIN; state = 100; }
                        else fail_identifier (ref state); break;

                    // a(rc)sin
                    case 100:
                        if (c == 'd') { current_ident = Ident.ASIND; state = 200; }
                        else fail_identifier (ref state); break;

                    // a(rc)t
                    case 101:
                        if (c == 'a') state = 102;
                        else fail_identifier (ref state); break;

                    // a(rc)ta
                    case 102:
                        if (c == 'n') { current_ident = Ident.ATAN; state = 103; }
                        else fail_identifier (ref state); break;

                    // a(rc)tan
                    case 103:
                        if (c == 'd') { current_ident = Ident.ATAND; state = 200; }
                        else fail_identifier (ref state); break;

                    case 200: fail_identifier (ref state); break;
                    default: assert_not_reached ();
                }

                if (!src.get_next_char (ref tmp_idx, out c) || !(c.isalnum () || c == 'π')) {
                    if (state == 10) {
                        current_ident = Ident.E;
                    } else if (current_ident == Ident.CUSTOM && !allow_custom_ident)
                        throw new MathError.UNKNOWN_FUNCTION ("invalid identifier");
                    break;
                }

                current_end = tmp_idx;
                c = c.tolower ();
            }
        }

        public inline void expect_end () throws MathError {
            if (current_type != TokenType.END)
                throw new MathError.SYNTAX ("trailing input");
        }

        public inline void expect (TokenType t) throws MathError {
            if (current_type != t)
                throw new MathError.SYNTAX ("expected token");
            next ();
        }

        public string get_current_token_as_string () {
            return src.substring (current_start, current_end - current_start);
        }
    }
}
