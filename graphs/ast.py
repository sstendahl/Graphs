# SPDX-License-Identifier: GPL-3.0-or-later
"""
Sympify an AST.
"""
import contextlib

from gi.repository import Graphs

import sympy
from sympy.core.function import Function


def disable_rewrite(sympy_class, name):
    class f(sympy_class):
        def _eval_simplify(self, **kwargs):
            return self

        def _sympystr(self, printer):
            return f"{name}({printer.doprint(self.args[0])})"

    return f


def deg_trig(sympy_func, name):
    class f(Function):
        @classmethod
        def eval(cls, x):
            if x.is_Number:
                return sympy_func(sympy.pi * x / 180)

        def _eval_rewrite_as_sympy(self, *args):
            x = self.args[0]
            return sympy_func(sympy.pi * x / 180)

    return disable_rewrite(f, name)


def deg_inv_trig(sympy_func, name):
    class f(Function):
        @classmethod
        def eval(cls, x):
            if x.is_Number:
                return 180 * sympy_func(x) / sympy.pi

        def _eval_rewrite_as_sympy(self, *args):
            x = self.args[0]
            return 180 * sympy_func(x) / sympy.pi

    return disable_rewrite(f, name)


FUNCTION_MAPPING = {
    Graphs.Ident.SIN: sympy.sin,
    Graphs.Ident.COS: sympy.cos,
    Graphs.Ident.TAN: sympy.tan,
    Graphs.Ident.COT: sympy.cot,
    Graphs.Ident.SEC: sympy.sec,
    Graphs.Ident.CSC: sympy.csc,
    Graphs.Ident.SIND: deg_trig(sympy.sin, "sind"),
    Graphs.Ident.COSD: deg_trig(sympy.cos, "cosd"),
    Graphs.Ident.TAND: deg_trig(sympy.tan, "tand"),
    Graphs.Ident.COTD: deg_trig(sympy.cot, "cotd"),
    Graphs.Ident.SECD: deg_trig(sympy.sec, "secd"),
    Graphs.Ident.CSCD: deg_trig(sympy.csc, "cscd"),
    Graphs.Ident.ASIN: sympy.asin,
    Graphs.Ident.ACOS: sympy.acos,
    Graphs.Ident.ATAN: sympy.atan,
    Graphs.Ident.ACOT: sympy.acot,
    Graphs.Ident.ASEC: sympy.asec,
    Graphs.Ident.ACSC: sympy.acsc,
    Graphs.Ident.ASIND: deg_inv_trig(sympy.asin, "asind"),
    Graphs.Ident.ACOSD: deg_inv_trig(sympy.acos, "acosd"),
    Graphs.Ident.ATAND: deg_inv_trig(sympy.atan, "atand"),
    Graphs.Ident.ACOTD: deg_inv_trig(sympy.acot, "acotd"),
    Graphs.Ident.ASECD: deg_inv_trig(sympy.asec, "asecd"),
    Graphs.Ident.ACSCD: deg_inv_trig(sympy.acsc, "acscd"),
    Graphs.Ident.SQRT: sympy.sqrt,
    Graphs.Ident.EXP: sympy.exp,
    Graphs.Ident.ABS: sympy.Abs,
}


def sympify(expr):
    """Sympify an Expression."""

    if isinstance(expr, Graphs.NumberExpression):
        return sympy.Float(expr.val)

    if isinstance(expr, Graphs.ConstantExpression):
        constant = expr.constant

        match constant:
            case Graphs.Ident.PI:
                return sympy.pi
            case Graphs.Ident.E:
                return sympy.E
            case Graphs.Ident.INF:
                return sympy.oo
            case _:
                raise ValueError(f"unsupported constant operator: {constant}")

    elif isinstance(expr, Graphs.VariableExpression):
        return sympy.Symbol(expr.name)

    elif isinstance(expr, Graphs.UnaryExpression):
        inner = sympify(expr.expr)

        match expr.op:
            case Graphs.TokenType.PLUS:
                return inner
            case Graphs.TokenType.MINUS:
                return -inner
            case _:
                raise ValueError(f"unsupported unary operator: {expr.op}")

    elif isinstance(expr, Graphs.BinaryExpression):
        left = sympify(expr.left)
        right = sympify(expr.right)

        match expr.op:
            case Graphs.TokenType.PLUS:
                return left + right
            case Graphs.TokenType.MINUS:
                return left - right
            case Graphs.TokenType.STAR:
                return left * right
            case Graphs.TokenType.SLASH:
                return left / right
            case Graphs.TokenType.CARET:
                return left ** right
            case _:
                raise ValueError(f"unsupported binary operator: {expr.op}")

    elif isinstance(expr, Graphs.FunctionExpression):
        arg = sympify(expr.arg)
        id = expr.ident

        with contextlib.suppress(KeyError):
            return FUNCTION_MAPPING[id](arg)

        match id:
            case Graphs.Ident.LOG:
                return sympy.log(arg, 10)
            case Graphs.Ident.LOG2:
                return sympy.log(arg, 2)
            case Graphs.Ident.LOG10:
                return sympy.log(arg, 10)
            case _:
                raise ValueError(f"unsupported function identifier: {id}")

    elif isinstance(expr, Graphs.PostfixExpression):
        match expr.op:
            case Graphs.TokenType.FACTORIAL:
                return sympy.factorial(sympify(expr.expr))
            case _:
                raise ValueError(f"unsupported postfix operator: {expr.op}")

    raise TypeError(f"unknown expression type: {type(expr)}")
