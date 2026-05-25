// SPDX-License-Identifier: GPL-3.0-or-later
void main (string[] args) {
    Test.init (ref args);

    // Add Test cases with functions here
    add_math_parser_tests ();

    Test.run ();
}
