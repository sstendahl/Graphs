// SPDX-License-Identifier: GPL-3.0-or-later
using Gee;

namespace Graphs.MathTools {
    private const double PI_THRESH = 0.00010000314159265359; // 1e-4 + 1e-9 * pi
    private const double E_THRESH = 0.00010000271828182846; // 1e-4 + 1e-9 * e

    /**
     * String representation of a double, prettifies for typical constants
     * such as integer values of pi and e.
     */
    public string prettyprint_double (double val) {
        if (val >= -PI_THRESH && val <= PI_THRESH) {
            return "0";
        }
        StringBuilder builder = new StringBuilder ();

        if (val < 0) {
            val *= -1;
            builder.append_c ('-');
        }

        // check if it is a multiple of pi
        double remainder = Math.fmod (val, Math.PI);
        if (remainder <= PI_THRESH || remainder >= Math.PI - PI_THRESH) {
            // fast rounding check evasion
            double factor = Math.floor (val / Math.PI + 0.5);
            if (factor != 1) builder.append ("%.15g".printf (factor));
            builder.append ("pi");
            return builder.free_and_steal ();
        }

        // or e
        remainder = Math.fmod (val, Math.E);
        if (remainder <= E_THRESH || remainder >= Math.E - E_THRESH) {
            // fast rounding check evasion
            double factor = Math.floor (val / Math.E + 0.5);
            if (factor != 1) builder.append ("%.15g".printf (factor));
            builder.append_c ('e');
            return builder.free_and_steal ();
        }

        builder.append ("%.15g".printf (val));
        return builder.free_and_steal ();
    }

    /**
     * Round a number to specified digits.
     */
    public static double sig_fig_round (double number, int digits) {
        if (number == 0) return 0.0;

        double abs_number = Math.fabs (number);
        int power = (int) Math.floor (Math.log10 (abs_number));

        int scale_power = digits - power - 1;
        double factor = Math.pow (10.0, scale_power);

        return Math.round (number * factor) / factor;
    }

    /**
     * Get all free variables (without x) in an equation.
     */
    public static string[] get_free_variables (string equation) throws MathError {
        HashSet<string> strings = new HashSet<string> ();

        MathParser.Lexer lexer = new MathParser.Lexer (true);
        lexer.start_lexing (equation);

        // we assume a correct input so we are only interested in custom idents
        while (lexer.current_type != MathParser.TokenType.END) {
            if (lexer.current_type == MathParser.TokenType.IDENT
                && lexer.current_ident == MathParser.Ident.CUSTOM) {
                string token = lexer.get_current_token_as_string ();
                if (token.down () != "x") strings.add (token);
            }

            lexer.next ();
        }

        return strings.to_array ();
    }
}
