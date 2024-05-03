# SPDX-License-Identifier: GPL-3.0-or-later
"""Various utility functions."""
import ast
import contextlib
import operator as op
import re

from gi.repository import Gio, Gtk

from graphs.misc import FUNCTIONS

import numpy

import sympy


def sig_fig_round(number: float, digits: int) -> float:
    """Round a number to the specified number of significant digits."""
    try:
        # Convert to scientific notation, and get power
        power = "{:e}".format(float(number)).split("e")[1]
    except IndexError:
        return None
    return round(float(number), -(int(power) - digits + 1))


def get_value_at_fraction(
    fraction: float,
    start: float,
    end: float,
    scale: int,
) -> float:
    """
    Get value at axis fraction.

    Obtain the selected value of an axis given at which percentage (in terms of
    fraction) of the length this axis is selected given the start and end range
    of this axis.
    """
    if scale == 0 or scale == 2:  # Linear or radian scale
        return start + fraction * (end - start)
    elif scale == 1:  # Logarithmic scale
        log_start = numpy.log10(start)
        log_end = numpy.log10(end)
        log_range = log_end - log_start
        log_value = log_start + log_range * fraction
        return pow(10, log_value)
    elif scale == 3:  # Square root scale
        # Use min limit as defined by scales.py
        start = max(0, start)
        sqrt_start = numpy.sqrt(start)
        sqrt_end = numpy.sqrt(end)
        sqrt_range = sqrt_end - sqrt_start
        sqrt_value = sqrt_start + sqrt_range * fraction
        return sqrt_value * sqrt_value
    elif scale == 4:  # Inverted scale (1/X)'
        # Use min limit as defined by scales.py if min equals zero
        start = end / 10 if end > 0 and start <= 0 else start
        scaled_range = 1 / start - 1 / end

        # Calculate the inverse-scaled value at the given percentage
        return 1 / (1 / end + fraction * scaled_range)


def get_fraction_at_value(
    value: float,
    start: float,
    end: float,
    scale: int,
) -> float:
    """
    Get fraction of axis at absolute value.

    Obtain the fraction of the total length of the selected axis a specific
    value corresponds to given the start and end range of the axis.
    """
    if scale == 0 or scale == 2:  # Linear or radian scale
        return (value - start) / (end - start)
    elif scale == 1:  # Logarithmic scale
        log_start = numpy.log10(start)
        log_end = numpy.log10(end)
        log_value = numpy.log10(value)
        log_range = log_end - log_start
        return (log_value - log_start) / log_range
    elif scale == 3:  # Square root scale
        # Use min limit as defined by scales.py
        start = max(0, start)
        sqrt_start = numpy.sqrt(start)
        sqrt_end = numpy.sqrt(end)
        sqrt_value = numpy.sqrt(value)
        sqrt_range = sqrt_end - sqrt_start
        return (sqrt_value - sqrt_start) / sqrt_range
    elif scale == 4:  # Inverted scale (1/X)
        # Use min limit as defined by scales.py if min equals zero
        start = end / 10 if end > 0 and start <= 0 else start
        scaled_range = 1 / start - 1 / end

        # Calculate the scaled percentage corresponding to the data point
        scaled_data_point = 1 / value
        return (scaled_data_point - 1 / end) / scaled_range


def create_file_filters(filters, add_all: bool = True) -> Gio.ListStore:
    """
    Create file filters.

    filters should be in the format:
    [
        (name, (suffix_a, suffix_b),
    ]
    """
    list_store = Gio.ListStore()
    for name, suffix_list in filters:
        file_filter = Gtk.FileFilter()
        file_filter.set_name(name)
        for suffix in suffix_list:
            file_filter.add_suffix(suffix)
        list_store.append(file_filter)
    if add_all:
        file_filter = Gtk.FileFilter()
        file_filter.set_name("All Files")
        file_filter.add_pattern("*")
        list_store.append(file_filter)
    return list_store


def string_to_float(string: str) -> float:
    """Evaluate a string represantation of a number."""
    try:
        return _eval(ast.parse(preprocess(string), mode="eval").body)
    except (SyntaxError, ValueError):
        return None


OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.BitXor: op.xor,
    ast.USub: op.neg,
}


def _eval(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return OPERATORS[type(node.op)](_eval(node.operand))
    else:
        raise ValueError


def preprocess(string: str) -> str:
    """Preprocess an equation to be compatible with numexpr syntax."""

    def convert_degrees(match):
        """Convert degree expressions to radian expressions."""
        function = match.group(1)
        if function in FUNCTIONS:
            expression = match.group(2)  # Get the content inside the brackets
            return f"{function}({expression}*{float(numpy.pi)}/180)"
        return f"{function}{expression}"

    def convert_cot(match):
        """Convert cotangent expressions to reciprocal tangent expressions."""
        expression = match.group(1)  # Get the content inside the brackets
        return f"1/(tan({expression}))"

    def convert_sec(match):
        """Convert secant expressions to reciprocal cosine expressions."""
        expression = match.group(1)  # Get the content inside the brackets
        return f"1/(cos({expression}))"

    def convert_csc(match):
        """Convert cosecant expressions to reciprocal sine expressions."""
        expression = match.group(1)  # Get the content inside the brackets
        return f"1/(sin({expression}))"

    def convert_arccot(match):
        """Convert arccotangent to reciprocal arcsine expressions."""
        expression = match.group(1)  # Get the content inside the brackets
        return f"arcsin(1/sqrt(1+{expression}**2))"

    def convert_arcsec(match):
        """Convert arcsecant to reciprocal cosine expressions."""
        expression = match.group(1)  # Get the content inside the brackets
        return f"(arccos(1/({expression})))"

    def convert_arccsc(match):
        """Convert arccosecant to reciprocal arcsine expressions."""
        expression = match.group(1)  # Get the content inside the brackets
        return f"(arcsin(1/({expression})))"

    def convert_superscript(match):
        """Convert superscript expressions to Python's power operator."""
        superscript_mapping = {
            "⁰": "0",
            "¹": "1",
            "²": "2",
            "³": "3",
            "⁴": "4",
            "⁵": "5",
            "⁶": "6",
            "⁷": "7",
            "⁸": "8",
            "⁹": "9",
        }
        sequence = match.group(1)  # Get the content inside the superscript
        sequence = "".join(
            superscript_mapping.get(char, char) for char in sequence
        )
        return f"**{sequence}"

    def add_asterix(match):
        """
        Add asterix to an equation.

        Adds asterix in equation when missing in case a number is followed
        by an alphabetical character, and adds parantheses around.

        Pattern is to check for least one digit, followed by at least one
        alphabetical character. e.g y = 24*x + 3sigma -> y = (24*x) + (3*sigma)
        """
        var, exp2 = match.group(1), match.group(2).lower()
        if var in FUNCTIONS:
            return f"{var}{exp2}"
        else:
            return f"{var}*{exp2}"

    string = string.replace(",", ".")
    string = re.sub(r"(\w+)d\((.*?)\)", convert_degrees, string)
    string = re.sub(r"(\d*\.?\d+)(?![Ee]?[-+]?\d)(\w+)", add_asterix, string)
    string = re.sub(r"(\w+)(\([\w\(]+)", add_asterix, string)
    string = string.replace("pi", f"({float(numpy.pi)})")
    string = string.replace("^", "**")
    string = string.replace(")(", ")*(")
    string = re.sub(r"arccot\((.*?)\)", convert_arccot, string)
    string = re.sub(r"arcsec\((.*?)\)", convert_arcsec, string)
    string = re.sub(r"arccsc\((.*?)\)", convert_arccsc, string)
    string = re.sub(r"cot\((.*?)\)", convert_cot, string)
    string = re.sub(r"sec\((.*?)\)", convert_sec, string)
    string = re.sub(r"csc\((.*?)\)", convert_csc, string)
    string = re.sub(
        r"([\u2070-\u209f\u00b0-\u00be]+)",
        convert_superscript,
        string,
    )
    return string.lower()


def string_to_function(equation_name: str) -> sympy.FunctionClass:
    """Convert a string into a sympy function."""
    variables = ["x"] + get_free_variables(equation_name)
    sym_vars = sympy.symbols(variables)
    with contextlib.suppress(sympy.SympifyError, TypeError, SyntaxError):
        symbolic = sympy.sympify(
            equation_name,
            locals=dict(zip(variables, sym_vars)),
        )
        return sympy.lambdify(sym_vars, symbolic)


def get_free_variables(equation_name: str) -> list:
    """Get the free variables (non-x) from an equation."""
    pattern = (
        r"\b(?!x\b|X\b"  # Exclude 'x' and 'X'
        r"|sec\b|sin\b|cos\b|log\b|tan\b|csc\b|cot\b"  # Exclude trig func.
        r"|arcsin\b|arccos\b|arctan\b"  # Exclude arctrig func.
        r"|arccot\b|arcsec\b|arccsc\b"  # Exclude arctrig func.
        r"|sinh\b|cosh\b|tanh\b"  # Exclude hyperbolicus argtrig func.
        r"|arcsinh\b|arccosh\b|arctanh\b"  # Exclude hyperb. arctrig func.
        r"|exp\b|sqrt\b|abs\b|log10\b)"  # Exclude 'exp', 'sqrt', 'abs'
        r"[a-zA-Z]+\b"  # Match any character sequence that is not excluded
    )
    return list(set(re.findall(pattern, equation_name)))
