// SPDX-License-Identifier: GPL-3.0-or-later
using Graphs;
using Graphs.MathParser;

private const double EPSILON = 1e-10;

private inline bool double_eq (double actual, double expected) {
    return Math.fabs (actual - expected) < EPSILON;
}

private void assert_evaluate_result (string expression, double expected) {
    try {
        double result = evaluate_string (expression);
        if (double_eq (result, expected)) return;

        Test.fail_printf ("%s should have been %lf, but was %lf", expression, expected, result);
    } catch (Error e) {
        Test.fail_printf ("%s: %s", expression, e.message);
    }
}

private void assert_throws_error (string expression, int code) {
    try {
        evaluate_string (expression);
        Test.fail_printf ("%s should have been invalid", expression);
    } catch (MathError e) {
        if (e.code != code)
            Test.fail_printf (e.message);
    }
}

private void test_basic_arithmetic () {
    assert_evaluate_result ("1+2", 3);
    assert_evaluate_result ("10-3", 7);
    assert_evaluate_result ("4*5", 20);
    assert_evaluate_result ("20/4", 5);
}

private void test_operator_precedence () {
    assert_evaluate_result ("2+3*4", 14);
    assert_evaluate_result ("(2+3)*4", 20);
    assert_evaluate_result ("2*3+4", 10);
}

private void test_power_associativity () {
    // right associative: 2^(3^2)
    assert_evaluate_result ("2^3^2", 512);
    assert_evaluate_result ("(2^3)^2", 64);
}

private void test_unary_operators () {
    assert_evaluate_result ("-5", -5);
    assert_evaluate_result ("+5", 5);
    assert_evaluate_result ("(-2)^2", 4);
}

private void test_factorial () {
    assert_evaluate_result ("0!", 1);
    assert_evaluate_result ("1!", 1);
    assert_evaluate_result ("5!", 120);
    assert_evaluate_result ("3!+2", 8);
}

private void test_implicit_multiplication () {
    assert_evaluate_result ("2(3+4)", 14);
    assert_evaluate_result ("2pi", 2 * Math.PI);
    assert_evaluate_result ("3sin(0)", 0);
    assert_evaluate_result ("(1+2)(3+4)", 21);
}

private void test_constants () {
    assert_evaluate_result ("pi", Math.PI);
    assert_evaluate_result ("e", Math.E);

    // We cannot check for error tolerance
    double inf;
    try_evaluate_string ("inf", out inf);
    assert_true (inf == double.INFINITY);
}

private void test_trig_functions_radians () {
    assert_evaluate_result ("sin(0)", 0);
    assert_evaluate_result ("cos(0)", 1);
    assert_evaluate_result ("tan(0)", 0);
    assert_evaluate_result ("sin(pi/2)", 1);
}

private void test_trig_functions_degrees () {
    assert_evaluate_result ("sind(90)", 1);
    assert_evaluate_result ("cosd(180)", -1);
    assert_evaluate_result ("tand(45)", 1);
}

private void test_inverse_trig_functions () {
    assert_evaluate_result ("asin(1)", Math.PI / 2);
    assert_evaluate_result ("acos(1)", 0);
    assert_evaluate_result ("atand(1)", 45);
}

private void test_misc_functions () {
    assert_evaluate_result ("sqrt(16)", 4);
    assert_evaluate_result ("abs(-5)", 5);
    assert_evaluate_result ("log(exp(1))", 1);
    assert_evaluate_result ("log10(1000)", 3);
    assert_evaluate_result ("log2(8)", 3);
}

private void test_nested_expressions () {
    assert_evaluate_result ("sqrt((2+3)*4)+sin(pi/2)", Math.sqrt (20) + 1);
}

private void test_decimal_separator () {
    double result;
    try_evaluate_string ("1,5+2,5", out result, ',');

    if (result != 4)
        Test.fail_printf ("could not swap decimal separator");
}

private void test_division_by_zero () {
    assert_throws_error ("1/0", MathError.INVALID);
}

private void test_invalid_factorial_negative () {
    assert_throws_error ("(-1)!", MathError.INVALID);
}

private void test_invalid_factorial_fractional () {
    assert_throws_error ("3.5!", MathError.INVALID);
}

private void test_operator_associativity () {
    // Subtraction is left-associative: (10 - 3) - 2 = 5
    assert_evaluate_result ("10-3-2", 5);

    // Division is left-associative: (20 / 4) / 2 = 2.5
    assert_evaluate_result ("20/4/2", 2.5);

    // Power is right-associative: 2^(3^2) = 512
    assert_evaluate_result ("2^3^2", 512);

    // Parentheses override the default associativity.
    assert_evaluate_result ("10-(3-2)", 9);
    assert_evaluate_result ("20/(4/2)", 10);
    assert_evaluate_result ("(2^3)^2", 64);

    // Factorial is postfix and binds tighter than exponentiation.
    assert_evaluate_result ("3!^2", 36);
    assert_evaluate_result ("2^3!", 64);
    assert_evaluate_result ("(3!)^2", 36);
    assert_evaluate_result ("2^(3!)", 64);

    // Repeated factorial is left-to-right as a postfix operation:
    // (3!)! = 720
    assert_evaluate_result ("3!!", 720);

    // Factorial combined with arithmetic associativity.
    assert_evaluate_result ("5!-4!-3!", 90);
    assert_evaluate_result ("5!/4!/3!", 0.83333333333333334);

    // Exponentiation remains right-associative when factorial is involved.
    // 1^(3!)^2 = 1^(720^2)
    assert_evaluate_result ("1^3!^2", Math.pow (1, 720 * 720));

    // Parentheses explicitly change the grouping.
    assert_evaluate_result ("(2^3!)^2", 4096);
    assert_evaluate_result ("2^(3!^2)", Math.pow (2, 36));

    // Unary operators vs exponentiation.
    assert_evaluate_result ("-2^2", -4);
    assert_evaluate_result ("(-2)^2", 4);
    assert_evaluate_result ("-2^3!", -64);
    assert_evaluate_result ("(-2)^3!", 64);

    // Unary operators combined with factorial.
    assert_evaluate_result ("-(3!)", -6);

    // Implicit multiplication combined with factorial and powers.
    assert_evaluate_result ("2*3!", 12);
    assert_evaluate_result ("2(3!)", 12);
    assert_evaluate_result ("2^3!", 64);
    assert_evaluate_result ("2(3!)^2", 72);

    // Function calls + factorial + powers.
    assert_evaluate_result ("sin(pi/2)^2", 1);
    assert_evaluate_result ("sqrt(3!)", Math.sqrt (6));
    assert_evaluate_result ("sqrt(3!)^2", 6);
    assert_evaluate_result ("(sqrt(3!))^2", 6);

    // Multiple levels of right-associative exponentiation.
    assert_evaluate_result ("2^2^3", 256);
    assert_evaluate_result ("2^2^3^1", 256);
    assert_evaluate_result ("2^(2^(3^1))", 256);

    // Factorials at different levels of an exponentiation chain.
    assert_evaluate_result ("2!^3", 8);
    assert_evaluate_result ("2^3!^2!", 68719476736);
    assert_evaluate_result ("(2!)^(3!)", 64);

    // Mixed implicit multiplication and exponentiation.
    assert_evaluate_result ("2^2(3!)", 24);
    assert_evaluate_result ("2(3^2)", 18);
    assert_evaluate_result ("(2^2)(3!)", 24);

    // Nested combinations.
    assert_evaluate_result ("2^(3!+1)", Math.pow (2, 7));
    assert_evaluate_result ("(2+3!)^2", 64);
    assert_evaluate_result ("2*(3!+2^3)", 28);
    assert_evaluate_result ("(2+3!)^(2+1)", 512);
}

private const string[] INVALID_SYNTAX = {
    "",
    "1+",
    "(1+2",
    "sin()",
    "*2",
    "2^^3"
};

private void test_syntax_errors () {
    foreach (unowned string expr in INVALID_SYNTAX) {
        assert_throws_error (expr, MathError.SYNTAX);
    }
}


void main (string[] args) {
    Test.init (ref args);

    Test.add_func ("/math-parser/eval/basic-arithmetic", test_basic_arithmetic);
    Test.add_func ("/math-parser/eval/operator-precedence", test_operator_precedence);
    Test.add_func ("/math-parser/eval/power-associativity", test_power_associativity);
    Test.add_func ("/math-parser/eval/unary-operators", test_unary_operators);
    Test.add_func ("/math-parser/eval/factorial", test_factorial);
    Test.add_func ("/math-parser/eval/implicit-multiplication", test_implicit_multiplication);
    Test.add_func ("/math-parser/eval/constants", test_constants);
    Test.add_func ("/math-parser/eval/trig-radians", test_trig_functions_radians);
    Test.add_func ("/math-parser/eval/trig-degrees", test_trig_functions_degrees);
    Test.add_func ("/math-parser/eval/inverse-trig", test_inverse_trig_functions);
    Test.add_func ("/math-parser/eval/misc-functions", test_misc_functions);
    Test.add_func ("/math-parser/eval/nested-expressions", test_nested_expressions);
    Test.add_func ("/math-parser/eval/decimal-separator", test_decimal_separator);
    Test.add_func ("/math-parser/eval/division-by-zero", test_division_by_zero);
    Test.add_func ("/math-parser/eval/invalid-factorial-negative", test_invalid_factorial_negative);
    Test.add_func ("/math-parser/eval/invalid-factorial-fractional", test_invalid_factorial_fractional);
    Test.add_func ("/math-parser/eval/operator-associativity", test_operator_associativity);
    Test.add_func ("/math-parser/eval/syntax-errors", test_syntax_errors);

    Test.run ();
}
