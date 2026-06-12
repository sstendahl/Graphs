# SPDX-License-Identifier: GPL-3.0-or-later
"""Python Helper - Python part."""
from gi.repository import Gio, Graphs

from graphs import (
    ast,
    curve_fitting,
    export_items,
    file_io,
    misc,
    operations,
)
from graphs.figure import Figure
from graphs.style_editor import PythonStyleEditor
from graphs.window import PythonWindow

import numpy

import sympy
from sympy.calculus.singularities import singularities

_REQUESTS = (
    "create-style-editor",
    "create-window",
    "curve-fitting-dialog",
    "export-figure",
    "export-items",
    "has-singularities",
    "perform-operation",
    "python-method",
    "simplify-expression",
)

XDATA = numpy.linspace(0, 10, 10)


class PythonHelper(Graphs.PythonHelper):
    """Python helper for python only calls."""

    def __init__(self):
        super().__init__()
        for request in _REQUESTS:
            request = request + "-request"
            self.connect(
                request,
                getattr(self, "_on_" + request.replace("-", "_")),
            )

    @staticmethod
    def _on_create_style_editor_request(self) -> Graphs.StyleEditor:
        return PythonStyleEditor()

    @staticmethod
    def _on_create_window_request(self) -> Graphs.Window:
        return PythonWindow()

    @staticmethod
    def _on_curve_fitting_dialog_request(
        self,
        window: Graphs.Window,
        item: Graphs.Item,
    ) -> None:
        return curve_fitting.CurveFittingDialog(window, item)

    @staticmethod
    def _on_export_items_request(
        self,
        window: Graphs.Window,
        mode: str,
        file: Gio.File,
        items: list[Graphs.Item],
        _n_items: int,
    ) -> None:
        figure_settings = window.get_data().get_figure_settings()
        return export_items.export_items(mode, file, items, figure_settings)

    @staticmethod
    def _on_export_figure_request(
        self,
        file: Gio.File,
        settings: Gio.Settings,
        data: Graphs.Data,
    ) -> None:
        with file_io.open(file, "wb") as file_like:
            figure = Figure(
                data.get_selected_style_params(),
                data,
                figure_settings=data.get_figure_settings(),
            )

            vector_formats = ["pdf", "eps", "ps", "svg"]
            fmt = settings.get_string("file-format")
            dpi = 100 if fmt.lower() in vector_formats else figure.get_dpi()
            width_inches = settings.get_int("width") / dpi
            height_inches = settings.get_int("height") / dpi
            figure.set_size_inches(width_inches, height_inches)
            figure.savefig(
                file_like,
                format=fmt,
                dpi=dpi,
                transparent=settings.get_boolean("transparent"),
                bbox_inches=None,
            )

    @staticmethod
    def _on_has_singularities_request(
        self,
        equation: str,
        xstart: float,
        xstop: float,
    ) -> None:
        domain = sympy.Interval(xstart, xstop)
        return singularities(ast.sympify(equation), misc.X, domain)

    @staticmethod
    def _on_perform_operation_request(
        self,
        window: Graphs.Window,
        name: str,
    ) -> None:
        operations.perform_operation(window, name)

    @staticmethod
    def _on_python_method_request(self, obj, method: str) -> None:
        getattr(obj, method)()

    @staticmethod
    def _on_simplify_expression_request(self, expression: str) -> str:
        return str(sympy.simplify(ast.sympify(expression)))
