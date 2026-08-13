// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathTools {
    private const double REL_TOL = 1e-9;
    private const double ABS_TOL = 1e-4;

    private const double PI_THRESH = 0.00010000314159265359; // 1e-4 + 1e-9 * pi
    private const double E_THRESH = 0.00010000271828182846; // 1e-4 + 1e-9 * e

    /**
     * Whether or not two values are close to each other.
     */
    public bool is_close (double a, double b) {
        return Math.fabs (a - b) <= Math.fmax (REL_TOL * Math.fmax (a.abs (), b.abs ()), ABS_TOL);
    }

    /**
     * Wether or not two values contain values close to each other.
     */
    public bool all_close (double[] a, double[] b)
        requires (a.length == b.length) {
        for (uint i = 0; i < a.length; i++) {
            if (!is_close (a[i], b[i])) return false;
        }
        return true;
    }

    /**
     * String representation of a double, prettifies for typical constants
     * such as integer values of pi and e.
     */
    public string prettyprint_double (double val) {
        if (val == 0) {
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
            if (factor != 0) {
                if (factor != 1) builder.append ("%.15g".printf (factor));
                builder.append ("pi");
                return builder.free_and_steal ();
            }
        }

        // or e
        remainder = Math.fmod (val, Math.E);
        if (remainder <= E_THRESH || remainder >= Math.E - E_THRESH) {
            // fast rounding check evasion
            double factor = Math.floor (val / Math.E + 0.5);
            if (factor != 0) {
                if (factor != 1) builder.append ("%.15g".printf (factor));
                builder.append_c ('e');
                return builder.free_and_steal ();
            }
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
        GenericSet<string> strings = new GenericSet<string> (str_hash, str_equal);

        MathParser.Lexer lexer = new MathParser.Lexer ();
        lexer.start_lexing (equation);

        // we assume a correct input so we are only interested in custom idents
        while (lexer.current_type != TokenType.END) {
            if (lexer.current_type == TokenType.IDENT
                && lexer.current_ident == Ident.CUSTOM) {
                string token = lexer.get_current_token_as_string ();
                if (token != "x") strings.add (token);
            }

            lexer.next ();
        }

        uint length = strings.length;
        string[] result = new string[length];
        var iter = strings.iterator ();
        for (int i = 0; i < length; i++) {
            result[i] = iter.next_value ();
        }
        return (owned) result;
    }

    public static double[] arange (int steps) {
        double[] result = new double[steps];
        CUtilities.arange (result);
        return result;
    }

    public static double[] evaluate_expression (Ast expr, int length, string variable) throws MathError {
        double[] input = arange (length);
        return ast_to_program (expr, variable).eval (input);
    }

    public static DataHolder program_to_data (Program program, double xstart, double xstop, int steps = 5000, Scale scale = Scale.LINEAR) throws MathError {
        double[] xdata = new double[steps];
        CUtilities.create_equidistant_data (xstart, xstop, scale, xdata);
        double[] ydata = program.eval (xdata);

        int filtered_size = CUtilities.filter_nonfinite (xdata, ydata, xdata.length);
        if (filtered_size < xdata.length) {
            xdata.resize (filtered_size);
            ydata.resize (filtered_size);
        }
        return new DataHolder ((owned) xdata, (owned) ydata, null, null);
    }

    public static DataHolder equation_to_data (Ast equation, double xstart, double xstop, int steps = 5000, Scale scale = Scale.LINEAR) throws MathError {
        return program_to_data (ast_to_program (equation), xstart, xstop, steps, scale);
    }


    public static double[] interpolate (
        double[] x_data,
        double[] y_data,
        double[] targets
    ) {
        double[] result = new double[targets.length];
        int point_count = int.min (x_data.length, y_data.length);

        if (point_count == 0) {
            return result;
        }

        int[] indices = new int[point_count];

        for (int i = 0; i < point_count; i++) {
            indices[i] = i;
        }

        qsort_with_data<int> (indices, sizeof (int), (index_a, index_b) => {
                    if (x_data[index_a] < x_data[index_b]) return -1;
                    if (x_data[index_a] > x_data[index_b]) return 1;
                    return 0;
                });

        for (int i = 0; i < targets.length; i++) {
            double target = targets[i];

            int first = indices[0];
            int last = indices[point_count - 1];

            if (target <= x_data[first]) {
                result[i] = y_data[first];
                continue;
            }

            if (target >= x_data[last]) {
                result[i] = y_data[last];
                continue;
            }

            int low = 0;
            int high = point_count - 1;

            while (high - low > 1) {
                int mid = (low + high) / 2;

                if (x_data[indices[mid]] <= target) {
                    low = mid;
                } else {
                    high = mid;
                }
            }

            int lower = indices[low];
            int upper = indices[high];

            double x_lower = x_data[lower];
            double x_upper = x_data[upper];
            double y_lower = y_data[lower];
            double y_upper = y_data[upper];

            double dx = x_upper - x_lower;

            result[i] = dx == 0
                ? y_lower
                : y_lower + (target - x_lower) / dx * (y_upper - y_lower);
        }

        return result;
    }

    private const double[] XDATA = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 };

    public static bool validate_expression (Ast expression) {
        try {
            double[] ydata = ast_to_program (expression).eval (XDATA);
            return CUtilities.finite_double (ydata);
        } catch (MathError e) {
            return false;
        }
    }

    public static bool validate_equation (string equation) {
        try {
            return validate_expression (expression_to_ast (equation));
        } catch (MathError e) {
            return false;
        }
    }
}
