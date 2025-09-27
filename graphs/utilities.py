# SPDX-License-Identifier: GPL-3.0-or-later
"""Various utility functions."""
import ast
import contextlib
import math
import operator as op
import re

from graphs import scales
from graphs.misc import FUNCTIONS

import numexpr

import numpy

from scipy.special import gamma

import sympy


def sig_fig_round(number: float, digits: int) -> float:
    """Round a number to the specified number of significant digits."""
    try:
        # Convert to scientific notation, and get power
        power = f"{float(number):e}".split("e")[1]
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
    match scales.Scale(scale):
        case scales.Scale.LINEAR | scales.Scale.RADIANS:
            return start + fraction * (end - start)
        case scales.Scale.LOG:
            log_start = numpy.log10(start)
            log_end = numpy.log10(end)
            log_range = log_end - log_start
            log_value = log_start + log_range * fraction
            return pow(10, log_value)
        case scales.Scale.LOG2:
            log_start = numpy.log2(start)
            log_end = numpy.log2(end)
            log_range = log_end - log_start
            log_value = log_start + log_range * fraction
            return pow(2, log_value)
        case scales.Scale.SQUAREROOT:
            # Use min limit as defined by scales.py
            sqrt_start = max(0, numpy.sqrt(start))
            sqrt_end = numpy.sqrt(end)
            sqrt_range = sqrt_end - sqrt_start
            # Square root value does not really work for negative fractions
            sqrt_value = sqrt_start + sqrt_range * max(0, fraction)
            return sqrt_value * sqrt_value
        case scales.Scale.INVERSE:
            # Use min limit as defined by scales.py if min equals zero
            start = end / 10 if start <= 0 < end else start
            scaled_range = 1 / start - 1 / end
            return 1 / (1 / end + fraction * scaled_range)
        case _:
            raise ValueError


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
    match scales.Scale(scale):
        case scales.Scale.LINEAR | scales.Scale.RADIANS:
            return (value - start) / (end - start)
        case scales.Scale.LOG:
            log_start = numpy.log10(start)
            log_end = numpy.log10(end)
            log_value = numpy.log10(value)
            log_range = log_end - log_start
            return (log_value - log_start) / log_range
        case scales.Scale.LOG2:
            log_start = numpy.log2(start)
            log_end = numpy.log2(end)
            log_value = numpy.log2(value)
            log_range = log_end - log_start
            return (log_value - log_start) / log_range
        case scales.Scale.SQUAREROOT:
            # Use min limit as defined by scales.py
            start = max(0, start)
            sqrt_start = numpy.sqrt(start)
            sqrt_end = numpy.sqrt(end)
            sqrt_value = numpy.sqrt(value)
            sqrt_range = sqrt_end - sqrt_start
            return (sqrt_value - sqrt_start) / sqrt_range
        case scales.Scale.INVERSE:
            # Use min limit as defined by scales.py if min equals zero
            start = end / 10 if start <= 0 < end else start
            scaled_range = 1 / start - 1 / end

            # Calculate the scaled percentage corresponding to the data point
            scaled_data_point = 1 / value
            return (scaled_data_point - 1 / end) / scaled_range
        case _:
            raise ValueError


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
    if isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return OPERATORS[type(node.op)](_eval(node.operand))
    raise ValueError


def factorial_function(x):
    """
    Factorial function using scipy's gamma function.

    For non-negative integers n, factorial(n) = gamma(n+1).
    This extends factorial to real numbers and handles arrays.
    """
    return gamma(numpy.array(x) + 1)


def extract_expression(remainder):
    """Isolate the expression within the first pair of parentheses."""
    stack = []
    stop_index = None
    for i, char in enumerate(remainder.lower()):
        if char == "(":
            stack.append(char)
        elif char == ")":
            stack.pop()
            if not stack:  # Matching parenthesis found
                stop_index = i + 1
                break
    if not stop_index:
        return remainder, ""
    expression = remainder[:stop_index]
    rest = remainder[stop_index:]
    return expression, rest


def preprocess(string: str) -> str:
    """Preprocess an equation to be compatible with numexpr syntax."""

    def convert_degrees(match):
        """Convert degree expressions to radian expressions."""
        function, remainder = match.group(1), match.group(2)
        if function not in FUNCTIONS:
            return f"{function}{remainder}"
        expression, rest = extract_expression(remainder)
        return f"{function}({expression}*{numpy.pi}/180){rest}"

    def convert_degrees_recursive(old_string):
        """Recursively convert degrees to match all parenthesis properly."""
        new_string = re.sub(r"(\w+)d(\(.*\))", convert_degrees, old_string)
        if new_string != old_string:
            return convert_degrees_recursive(new_string)
        return new_string

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

    # --- Factorial handling ---
    def convert_factorial(match_start_end):
        start, end, expr_part = match_start_end
        func_match = re.match(r"\w*$", expr_part[:start])
        function = func_match.group(0) if func_match else ""
        if function not in FUNCTIONS:
            return f"factorial({expr_part})"
        return f"factorial({function}{expr_part})"

    def find_factorials(equation: str):
        """Greedy factorial finder handling nested parentheses/functions."""
        results = []
        i = 0
        while i < len(equation):
            if equation[i] == "!":
                rev_part = equation[:i][::-1]
                m = re.match(r".+", rev_part)
                if m:
                    expr_part = m.group(0)[::-1]
                    results.append((i - len(expr_part), i + 1, expr_part))
                i += 1
            else:
                i += 1
        return results

    def convert_factorial_recursive(expr: str) -> str:
        """Recursively replace factorials."""
        factorial_pattern = \
            re.compile(r"(\w+\(.*?\)|\([^()]*\)|\d+(?:\.\d+)?|\w)!")

        def convert_factorial(match):
            expr_part = match.group(1)
            return f"factorial({expr_part})"

        new_expr = re.sub(factorial_pattern, convert_factorial, expr)
        if new_expr != expr:
            return convert_factorial_recursive(new_expr)
        return new_expr

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
        return f"{var}*{exp2}"

    string = string.lower()
    string = string.replace(",", ".")
    string = convert_degrees_recursive(string)
    string = re.sub(
        r"([\u2070-\u209f\u00b0-\u00be]+)",
        convert_superscript,
        string,
    )

    string = convert_factorial_recursive(string)
    string = re.sub(r"(\d*\.?\d+)(?![Ee]?[-+]?\d)(\w+)", add_asterix, string)
    string = re.sub(r"(\w+)(\([\w\(]+)", add_asterix, string)
    string = string.replace("π", "pi").replace("pi", f"({float(numpy.pi)})")
    string = string.replace("^", "**")
    string = string.replace(")(", ")*(")
    string = re.sub(r"arccot\((.*?)\)", convert_arccot, string)
    string = re.sub(r"arcsec\((.*?)\)", convert_arcsec, string)
    string = re.sub(r"arccsc\((.*?)\)", convert_arccsc, string)
    string = re.sub(r"cot\((.*?)\)", convert_cot, string)
    string = re.sub(r"sec\((.*?)\)", convert_sec, string)
    return re.sub(r"csc\((.*?)\)", convert_csc, string)


def prettify_equation(equation: str) -> str:
    """Return an equation in a prettier, more humanly readable, format."""

    def reformat_pi(match):
        """
        Turn an integer amount of pi from SymPy into the format `npi`.

        Here n is an integer number.
        """
        number_string = match.group(1)
        number = float(number_string)
        if numpy.allclose(number % numpy.pi, 0, rtol=1e-04):
            int_pi = math.floor(number / numpy.pi)
            number_string = "pi" if int_pi == 1 else f"{int_pi}pi"
        return number_string

    equation = equation.replace(" ", "")
    equation = re.sub(r"(\d+\.\d+)", reformat_pi, equation)
    equation = equation.replace("**", "^")
    equation = re.sub(r"factorial\(([^)]+)\)", r"\1!", equation)
    return equation.replace(")*(", ")(")


def create_equidistant_xdata(
    limits: tuple,
    scale: int = 1,
    steps: int = 5000,
) -> list:
    """Generate evenly-spaced x-values on the given scale."""
    x_start, x_stop = limits
    scale = scales.Scale(scale)
    match scale:
        case scales.Scale.LINEAR | scales.Scale.RADIANS:
            xdata = numpy.linspace(x_start, x_stop, steps).tolist()
        case scales.Scale.LOG:
            x_start = max(x_start, 1e-300)
            x_stop = x_stop if numpy.isfinite(x_stop) else 1e300
            xdata = numpy.logspace(
                numpy.log10(x_start),
                numpy.log10(x_stop),
                steps,
            ).tolist()
        case scales.Scale.LOG2:
            x_start = max(x_start, 1e-300)
            x_stop = x_stop if numpy.isfinite(x_stop) else 1e300
            xdata = numpy.logspace(
                numpy.log2(x_start),
                numpy.log2(x_stop),
                steps,
                base=2,
            ).tolist()
        case scales.Scale.SQUAREROOT:
            x_start = max(x_start, 1e-300)
            xdata = numpy.linspace(
                numpy.sqrt(x_start),
                numpy.sqrt(x_stop),
                steps,
            )
            xdata = (xdata**2).tolist()
        case scales.Scale.INVERSE:
            xdata = \
                (1 / numpy.linspace(1 / x_start, 1 / x_stop, steps)).tolist()
        case _:
            raise ValueError
    return xdata


def equation_to_data(
    equation: str,
    limits: tuple = None,
    steps: int = 5000,
    scale: int = 0,
) -> tuple:
    """Convert an equation into data over a specified range of x-values."""
    if limits is None:
        limits = (0, 10)
    equation = preprocess(equation)
    xdata = create_equidistant_xdata(limits, scale, steps)

    try:
        equation = _precompute_factorials(equation, xdata)
        ydata = numpy.ndarray.tolist(
            _evaluate_equation(equation, local_dict={"x": xdata}),
        )
    except (KeyError, SyntaxError, ValueError, TypeError):
        return None, None
    return xdata, ydata


def _is_float(expr: str) -> bool:
    """Check if expression is a simple numeric constant."""
    try:
        float(expr)
        return True
    except ValueError:
        return False


class FactorialProcessor:
    """Handles factorial expression processing and variable management."""

    def __init__(self):
        self.computed_vars = {}
        self.var_counter = 0

    def get_next_var_name(self) -> str:
        """Generate next variable name for substitution."""
        name = f"gamma_var_{self.var_counter}"
        self.var_counter += 1
        return name

    def store_computed_values(self, var_name: str, values: numpy.ndarray):
        """Store computed factorial values for later substitution."""
        self.computed_vars[var_name] = values

    def clear_vars(self):
        """Clear stored variables after use."""
        self.computed_vars.clear()
        self.var_counter = 0


def _find_factorial_calls(equation: str):
    """Handle nested parentheses for factorials using extract_expression."""
    results = []
    i = 0
    while i < len(equation):
        if equation.startswith("factorial", i):
            start = i
            inner_expr, rest = \
                extract_expression(equation[i + len("factorial"):])
            end = i + len("factorial") + len(inner_expr)
            results.append((start, end, inner_expr[1:-1]))
            i = end
        else:
            i += 1
    return results


def _precompute_factorials(equation: str, xdata: list) -> str:
    """Pre-compute factorial expressions and substitute them in equation."""
    processor = FactorialProcessor()
    x_array = numpy.array(xdata)

    def process(expr: str) -> str:
        expr = expr.strip()
        # Resolve inner factorials first
        expr = _replace_factorials(expr)

        if _is_float(expr):
            return str(float(gamma(float(expr) + 1)))
        elif expr == "x":
            var_name = processor.get_next_var_name()
            processor.store_computed_values(var_name, gamma(x_array + 1))
            return var_name
        else:
            values = numexpr.evaluate(expr, local_dict={"x": x_array})
            factorial_values = gamma(values + 1)
            var_name = processor.get_next_var_name()
            processor.store_computed_values(var_name, factorial_values)
            return var_name

    def _replace_factorials(eq: str) -> str:
        while True:
            calls = _find_factorial_calls(eq)
            if not calls:
                break
            # Replace from right to left to avoid shifting indices
            for start, end, inner in reversed(calls):
                replacement = process(inner)
                eq = eq[:start] + replacement + eq[end:]
        return eq

    final_equation = _replace_factorials(equation)
    _precompute_factorials.processor = processor
    return final_equation


def _evaluate_equation(expr: str, local_dict: dict = None) -> numpy.ndarray:
    """Evaluate expression, including pre-computed factorial variables."""
    if local_dict is None:
        local_dict = {}

    if hasattr(_precompute_factorials, "processor"):
        local_dict.update(_precompute_factorials.processor.computed_vars)
        _precompute_factorials.processor.clear_vars()

    return numexpr.evaluate(expr, local_dict=local_dict)


def validate_equation(equation: str, limits: tuple = None) -> bool:
    """Validate whether an equation can be parsed."""
    equation = preprocess(equation)
    validate, _ = equation_to_data(equation, limits, steps=10)
    return validate is not None


def string_to_function(equation_name: str) -> sympy.FunctionClass:
    """Convert a string into a sympy function."""
    variables = ["x"] + get_free_variables(equation_name)
    sym_vars = sympy.symbols(variables)
    with contextlib.suppress(sympy.SympifyError, TypeError, SyntaxError):
        local_dict = dict(zip(variables, sym_vars))
        local_dict["factorial"] = sympy.factorial
        symbolic = sympy.sympify(
            equation_name,
            locals=local_dict,
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
        r"|factorial\b)"  # Exclude 'factorial' function
        r"[a-zA-Z]+\b"  # Match any character sequence that is not excluded
    )
    return list(set(re.findall(pattern, equation_name)))
