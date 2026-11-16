# SPDX-License-Identifier: GPL-3.0-or-later
"""Curve fitting module."""
from gi.repository import Graphs

from graphs import ast, utilities

import numpy

from scipy.optimize import _minpack, curve_fit

import sympy


def fit_curve(
    problem: Graphs.FitProblem,
    result: Graphs.FitResult,
) -> Graphs.CurveFittingError:
    """Solve a Curve Fitting Problem."""
    variables = ["x"] + problem.free_vars
    sym_vars = sympy.symbols(variables)
    sym_params_map = dict(zip(variables, sym_vars))
    x_data, y_data = utilities.get_xydata(problem.data)
    fitting_params = problem.parameters
    p0 = list(map(lambda x: x.get_initial(), fitting_params))
    lower_bounds = list(map(lambda x: x.get_lower_bound(), fitting_params))
    upper_bounds = list(map(lambda x: x.get_upper_bound(), fitting_params))

    try:
        symbolic = ast.sympify(problem.expression)
        func = sympy.lambdify(sym_vars, symbolic, modules="scipy")
        params, param_cov = curve_fit(
            func, x_data, y_data,
            p0=p0,
            bounds=(lower_bounds, upper_bounds),
            nan_policy="omit",
            method=problem.settings.get_string("optimization"),
        )
    except (sympy.SympifyError, TypeError, SyntaxError):
        return Graphs.CurveFittingError.EQUATION
    except (RuntimeError, _minpack.error):
        return Graphs.CurveFittingError.CONVERGENCE
    except (ValueError, ZeroDivisionError, OverflowError):
        return Graphs.CurveFittingError.DOMAIN

    if numpy.any(numpy.isinf(param_cov)):
        return Graphs.CurveFittingError.SINGULAR

    # Calculate statistics
    residuals = y_data - func(x_data, *params)
    ss_res = numpy.sum(residuals**2)
    ss_tot = numpy.sum((y_data - numpy.mean(y_data))**2)
    result.set_parameters(params)
    result.set_diag_covars(numpy.sqrt(numpy.diagonal(param_cov)))
    result.r2 = 1 - (ss_res / ss_tot)
    result.rmse = numpy.sqrt(ss_res / y_data.size)
    result.residuals = Graphs.DataHolder.new(x_data, residuals, None, None)

    # Substitute each free variables with the calculated value.
    values = dict(zip(problem.free_vars, params))
    fitted_eq = str(sympy.simplify(symbolic.subs(values)))
    fitted_eq = Graphs.expression_to_ast(fitted_eq)
    fitted_eq = Graphs.ast_to_expression(fitted_eq)
    result.fitted_equation_string = fitted_eq

    x_fit = utilities.bytes_to_ndarray(problem.x_fit)
    y_fit = func(x_fit, *params)
    if numpy.ndim(y_fit) == 0:
        y_fit = numpy.full(x_fit.size, y_fit.item())
    result.fit = Graphs.DataHolder.new(x_fit, y_fit, None, None)

    # Calculate and update confidence band for error propagation.
    jacobian = numpy.column_stack([
        numpy.full(x_fit.size, g) if numpy.ndim(
            g := sympy.lambdify(
                sym_vars,
                sympy.diff(symbolic, sym_params_map[name]),
                modules="scipy",
            )(x_fit, *params),
        ) == 0 else g for name in problem.free_vars
    ])
    variance = numpy.sum(jacobian * (jacobian @ param_cov), axis=1)

    std_dev_y = numpy.sqrt(numpy.abs(variance))
    confidence_band = std_dev_y * problem.settings.get_enum("confidence")

    y_upper = y_fit + confidence_band
    y_lower = y_fit - confidence_band
    result.confidence = Graphs.FillHolder.new(x_fit, y_lower, y_upper)

    return Graphs.CurveFittingError.NONE
