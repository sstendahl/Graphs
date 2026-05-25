# SPDX-License-Identifier: GPL-3.0-or-later
"""Sympify an AST."""
import contextlib

from gi.repository import Graphs

import sympy
from sympy.core.function import Function


def _disable_rewrite(sympy_class, name):
    class F(sympy_class):
        def _eval_simplify(self, **_kwargs):
            return self

        def _sympystr(self, printer):
            return f"{name}({printer.doprint(self.args[0])})"

    return F


def _deg_trig(sympy_func, name):
    class F(Function):
        @classmethod
        def eval(cls, x):
            if x.is_Number:
                return sympy_func(sympy.pi * x / 180)

        def _eval_rewrite_as_sympy(self, *_args):
            x = self.args[0]
            return sympy_func(sympy.pi * x / 180)

    return _disable_rewrite(F, name)


def _deg_inv_trig(sympy_func, name):
    class F(Function):
        @classmethod
        def eval(cls, x):
            if x.is_Number:
                return 180 * sympy_func(x) / sympy.pi

        def _eval_rewrite_as_sympy(self, *_args):
            x = self.args[0]
            return 180 * sympy_func(x) / sympy.pi

    return _disable_rewrite(F, name)


FUNCTION_MAPPING = {
    Graphs.Ident.SIN: sympy.sin,
    Graphs.Ident.COS: sympy.cos,
    Graphs.Ident.TAN: sympy.tan,
    Graphs.Ident.COT: sympy.cot,
    Graphs.Ident.SEC: sympy.sec,
    Graphs.Ident.CSC: sympy.csc,
    Graphs.Ident.SIND: _deg_trig(sympy.sin, "sind"),
    Graphs.Ident.COSD: _deg_trig(sympy.cos, "cosd"),
    Graphs.Ident.TAND: _deg_trig(sympy.tan, "tand"),
    Graphs.Ident.COTD: _deg_trig(sympy.cot, "cotd"),
    Graphs.Ident.SECD: _deg_trig(sympy.sec, "secd"),
    Graphs.Ident.CSCD: _deg_trig(sympy.csc, "cscd"),
    Graphs.Ident.ASIN: sympy.asin,
    Graphs.Ident.ACOS: sympy.acos,
    Graphs.Ident.ATAN: sympy.atan,
    Graphs.Ident.ACOT: sympy.acot,
    Graphs.Ident.ASEC: sympy.asec,
    Graphs.Ident.ACSC: sympy.acsc,
    Graphs.Ident.ASIND: _deg_inv_trig(sympy.asin, "asind"),
    Graphs.Ident.ACOSD: _deg_inv_trig(sympy.acos, "acosd"),
    Graphs.Ident.ATAND: _deg_inv_trig(sympy.atan, "atand"),
    Graphs.Ident.ACOTD: _deg_inv_trig(sympy.acot, "acotd"),
    Graphs.Ident.ASECD: _deg_inv_trig(sympy.asec, "asecd"),
    Graphs.Ident.ACSCD: _deg_inv_trig(sympy.acsc, "acscd"),
    Graphs.Ident.SQRT: sympy.sqrt,
    Graphs.Ident.EXP: sympy.exp,
    Graphs.Ident.ABS: sympy.Abs,
}


def sympify(expr):
    """Sympify an Expression."""
    if isinstance(expr, Graphs.NumberExpression):
        return sympy.Float(expr.val())

    if isinstance(expr, Graphs.ConstantExpression):
        constant = expr.constant()

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
        return sympy.Symbol(expr.name())

    elif isinstance(expr, Graphs.UnaryExpression):
        inner = sympify(expr.expr())
        op = expr.op()

        match op:
            case Graphs.TokenType.PLUS:
                return inner
            case Graphs.TokenType.MINUS:
                return -inner
            case _:
                raise ValueError(f"unsupported unary operator: {op}")

    elif isinstance(expr, Graphs.BinaryExpression):
        left = sympify(expr.left())
        right = sympify(expr.right())
        op = expr.op()

        match op:
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
            case Graphs.TokenType.SUPERSCRIPT:
                return left ** right
            case _:
                raise ValueError(f"unsupported binary operator: {op}")

    elif isinstance(expr, Graphs.FunctionExpression):
        arg = sympify(expr.arg())
        ident = expr.ident()

        with contextlib.suppress(KeyError):
            return FUNCTION_MAPPING[ident](arg)

        match ident:
            case Graphs.Ident.LOG:
                return sympy.log(arg, 10)
            case Graphs.Ident.LOG2:
                return sympy.log(arg, 2)
            case Graphs.Ident.LOG10:
                return sympy.log(arg, 10)
            case _:
                raise ValueError(f"unsupported function identifier: {ident}")

    elif isinstance(expr, Graphs.PostfixExpression):
        arg = sympify(expr.expr())
        op = expr.op()

        match op:
            case Graphs.TokenType.FACT:
                return sympy.factorial(arg)
            case _:
                raise ValueError(f"unsupported postfix operator: {op}")

    raise TypeError(f"unknown expression type: {type(expr)}")
