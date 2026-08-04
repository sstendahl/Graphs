// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    [Compact]
    private class Lexer {
        public unowned string src;
        public unichar c;
        public unichar decimal_separator;

        public TokenType current_type;
        public Operator current_op;
        public Ident current_ident;
        public double current_val;

        public int current_start;
        public int current_end;

        public void start_lexing (string src, unichar decimal_separator = '.') throws MathError {
            this.src = src;
            this.current_end = 0;
            this.decimal_separator = decimal_separator;
            next ();
        }

        private inline void set_superscript (int val) {
            current_type = TokenType.OPERATOR;
            current_op = Operator.SUPERSCRIPT;
            current_val = val;
        }

        public void next () throws MathError {
            current_start = current_end;
            while (true) {
                if (src.get_next_char (ref current_end, out c)) {
                    if (!c.isspace ()) break;
                    current_start = current_end;
                    continue;
                }
                if (current_end == 0) throw new MathError.SYNTAX ("empty expression");
                current_type = TokenType.END;
                return;
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
                    current_type = TokenType.OPERATOR;
                    current_op = Operator.POW;
                    current_end = tmp_idx;
                } else {
                    current_type = TokenType.OPERATOR;
                    current_op = Operator.MUL;
                }
                return;
            }

            if (c == '+' || c == '-') {
                // look ahead and resolve stacked unary operators
                bool plus = c == '+';
                int tmp_idx = current_end;
                while (true) {
                    do {
                        if (!src.get_next_char (ref tmp_idx, out c))
                            throw new MathError.SYNTAX ("expected token");
                    } while (c.isspace ());
                    if (c == '-') plus = !plus;
                    else if (c != '+') break;
                    current_end = tmp_idx;
                }
                current_type = TokenType.OPERATOR;
                current_op = plus ? Operator.ADD : Operator.SUB;
                return;
            }

            // Single-character token
            switch (c) {
                case '/': current_type = TokenType.OPERATOR; current_op = Operator.DIV; break;
                case '^': current_type = TokenType.OPERATOR; current_op = Operator.POW; break;
                case '!': current_type = TokenType.OPERATOR; current_op = Operator.FACT; break;
                case '(': current_type = TokenType.LPAREN; break;
                case ')': current_type = TokenType.RPAREN; break;
                // Superscript
                case '⁰': set_superscript (0); break;
                case '¹': set_superscript (1); break;
                case '²': set_superscript (2); break;
                case '³': set_superscript (3); break;
                case '⁴': set_superscript (4); break;
                case '⁵': set_superscript (5); break;
                case '⁶': set_superscript (6); break;
                case '⁷': set_superscript (7); break;
                case '⁸': set_superscript (8); break;
                case '⁹': set_superscript (9); break;
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

        private static inline bool is_superscript (unichar c) {
            switch (c) {
                case '⁰': case '¹': case '²': case '³': case '⁴': case '⁵':
                case '⁶': case '⁷': case '⁸': case '⁹': return true;
                default: return false;
            }
        }

        private enum TrieState {
            NONE,
            CUSTOM,

            A, AB,
               AC, ACO, ACOS,
                        ACOT,
                   ACS, ACSC,
               AR, ARC,
               AS, ASE, ASEC,
                   ASI, ASIN,
               AT, ATA, ATAN,
            C, CO, COS,
                   COT,
               CS, CSC,
            E, EX,
            I, IN,
            L, LO, LOG, LOG1,
            P,
            S, SE, SEC,
               SI, SIN,
               SQ, SQR,
            T, TA, TAN,

        }

        private void handle_identifier () {
            current_type = TokenType.IDENT;
            current_ident = Ident.CUSTOM;

            TrieState state = TrieState.NONE;
            int tmp_idx = current_end;

            c = c.tolower ();
            while (true) {
                // process current char in trie
                switch (state) {
                    case TrieState.NONE:
                        switch (c) {
                            case 'π': {
                                current_ident = Ident.PI;
                                state = TrieState.CUSTOM;
                                break;
                            }
                            case 'p': state = TrieState.P; break;
                            case 'e': state = TrieState.E; break;
                            case 'i': state = TrieState.I; break;
                            case 's': state = TrieState.S; break;
                            case 'c': state = TrieState.C; break;
                            case 't': state = TrieState.T; break;
                            case 'l': state = TrieState.L; break;
                            case 'a': state = TrieState.A; break;
                            default:
                                current_ident = Ident.CUSTOM;
                                state = TrieState.CUSTOM;
                                break;
                        }
                        break;

                    case TrieState.CUSTOM:
                        current_ident = Ident.CUSTOM;
                        state = TrieState.CUSTOM;
                        break;

                    case TrieState.A:
                        if (c == 'b') state = TrieState.AB;
                        else if (c == 'c') state = TrieState.AC;
                        else if (c == 'r') state = TrieState.AR;
                        else if (c == 's') state = TrieState.AS;
                        else if (c == 't') state = TrieState.AT;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.AB:
                        if (c == 's') { current_ident = Ident.ABS; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.AC:
                        if (c == 'o') state = TrieState.ACO;
                        else if (c == 's') state = TrieState.ACS;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ACO:
                        if (c == 's') { current_ident = Ident.ACOS; state = TrieState.ACOS; }
                        else if (c == 't') { current_ident = Ident.ACOT; state = TrieState.ACOT; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ACOS:
                        if (c == 'd') { current_ident = Ident.ACOSD; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ACOT:
                        if (c == 'd') { current_ident = Ident.ACOTD; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ACS:
                        if (c == 'c') { current_ident = Ident.ACSC; state = TrieState.ACSC; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ACSC:
                        if (c == 'd') { current_ident = Ident.ACSCD; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.AR:
                        if (c == 'c') state = TrieState.ARC;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    // we support writing arc* as a*
                    case TrieState.ARC:
                        if (c == 'c') state = TrieState.AC;
                        else if (c == 's') state = TrieState.AS;
                        else if (c == 't') state = TrieState.AT;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.AS:
                        if (c == 'e') state = TrieState.ASE;
                        else if (c == 'i') state = TrieState.ASI;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ASE:
                        if (c == 'c') { current_ident = Ident.ASEC; state = TrieState.ASEC; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ASEC:
                        if (c == 'd') { current_ident = Ident.ASECD; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ASI:
                        if (c == 'n') { current_ident = Ident.ASIN; state = TrieState.ASIN; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ASIN:
                        if (c == 'd') { current_ident = Ident.ASIND; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.AT:
                        if (c == 'a') state = TrieState.ATA;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ATA:
                        if (c == 'n') { current_ident = Ident.ATAN; state = TrieState.ATAN; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.ATAN:
                        if (c == 'd') { current_ident = Ident.ATAND; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.C:
                        if (c == 'o') state = TrieState.CO;
                        else if (c == 's') state = TrieState.CS;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.CO:
                        if (c == 's') { current_ident = Ident.COS; state = TrieState.COS; }
                        else if (c == 't') { current_ident = Ident.COT; state = COT; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.COS:
                        if (c == 'd') { current_ident = Ident.COSD; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.COT:
                        if (c == 'd') { current_ident = Ident.COTD; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.CS:
                        if (c == 'c') { current_ident = Ident.CSC; state = TrieState.CSC; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.CSC:
                        if (c == 'd') { current_ident = Ident.CSCD; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.E:
                        if (c == 'x') state = TrieState.EX;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.EX:
                        if (c == 'p') { current_ident = Ident.EXP; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.I:
                        if (c == 'n') state = TrieState.IN;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.IN:
                        if (c == 'f') { current_ident = Ident.INF; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.L:
                        if (c == 'n') { current_ident = Ident.LN; state = TrieState.CUSTOM; }
                        else if (c == 'o') state = TrieState.LO;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.LO:
                        if (c == 'g') { current_ident = Ident.LN; state = TrieState.LOG; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.LOG:
                        if (c == '2') { current_ident = Ident.LOG2; state = TrieState.CUSTOM; }
                        else if (c == '1') { current_ident = Ident.CUSTOM; state = TrieState.LOG1; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.LOG1:
                        if (c == '0') { current_ident = Ident.LOG10; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.P:
                        if (c == 'i') { current_ident = Ident.PI; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.S:
                        if (c == 'e') state = TrieState.SE;
                        else if (c == 'i') state = TrieState.SI;
                        else if (c == 'q') state = TrieState.SQ;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.SE:
                        if (c == 'c') { current_ident = Ident.SEC; state = TrieState.SEC; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.SEC:
                        if (c == 'd') { current_ident = Ident.SECD; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.SI:
                        if (c == 'n') { current_ident = Ident.SIN; state = TrieState.SIN; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.SIN:
                        if (c == 'd') { current_ident = Ident.SIND; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.SQ:
                        if (c == 'r') state = TrieState.SQR;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.SQR:
                        if (c == 't') { current_ident = Ident.SQRT; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.T:
                        if (c == 'a') state = TrieState.TA;
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.TA:
                        if (c == 'n') { current_ident = Ident.TAN; state = TrieState.TAN; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    case TrieState.TAN:
                        if (c == 'd') { current_ident = Ident.TAND; state = TrieState.CUSTOM; }
                        else { current_ident = Ident.CUSTOM; state = TrieState.CUSTOM; } break;

                    default: assert_not_reached ();
                }

                if (!src.get_next_char (ref tmp_idx, out c)
                    || !(c.isalnum () || c == 'π')
                    || is_superscript (c)) {
                    if (state == 10) current_ident = Ident.E;
                    break;
                }

                current_end = tmp_idx;
                c = c.tolower ();
            }
        }

        public string get_current_token_as_string () {
            char[] chars = new char[current_end - current_start];
            int j = 0;
            for (int i = current_start; i < current_end; i++) {
                chars[j++] = src[i].tolower ();
            }
            return (string) ((owned) chars);
        }
    }
}
