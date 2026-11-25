# SPDX-License-Identifier: GPL-3.0-or-later
"""Python Helper - Python part."""
import io

from gi.repository import GLib, Gdk, Gio, Graphs

import gio_pyio

from graphs import ast, curve_fitting, operations
from graphs.canvas.canvas import Canvas
from graphs.canvas.figure import Figure
from graphs.window import PythonWindow

from matplotlib import rcParams, rcParamsDefault

import sympy
from sympy.abc import x
from sympy.calculus.singularities import singularities

_REQUESTS = (
    "copy-figure",
    "create-canvas",
    "create-window",
    "curve-fit",
    "export-figure",
    "has-singularities",
    "perform-operation",
    "python-method",
    "simplify-expression",
)

FIGURE_IGNORELIST = (
    "custom_style",
    "use_custom_style",
    "min_selected",
    "max_selected",
    "hide_unselected",
    "lock_min_bottom",
    "lock_max_bottom",
    "lock_min_top",
    "lock_max_top",
    "lock_min_left",
    "lock_max_left",
    "lock_min_right",
    "lock_max_right",
)


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
    def _on_create_canvas_request(
        self,
        params: Graphs.StyleParameters,
        items: Gio.ListModel,
        interactive: bool,
        figure_settings: Graphs.FigureSettings,
    ) -> Graphs.Canvas:
        rcParams.update(rcParamsDefault)
        canvas = Canvas(
            params,
            items,
            interactive=interactive,
            figure_settings=figure_settings,
        )

        if figure_settings is not None:
            for prop in dir(figure_settings.props):
                if prop in FIGURE_IGNORELIST:
                    continue
                figure_settings.bind_property(prop, canvas.figure, prop, 1)

        return canvas

    @staticmethod
    def _on_create_window_request(self) -> Graphs.Window:
        return PythonWindow()

    @staticmethod
    def _on_curve_fit_request(
        self,
        problem: Graphs.FitProblem,
        result: Graphs.FitResult,
    ) -> Graphs.CurveFittingError:
        return curve_fitting.fit_curve(problem, result)

    @staticmethod
    def _on_copy_figure_request(
        self,
        data: Graphs.Data,
        width: int,
        height: int,
    ) -> None:
        """Copy the figure at the size it is shown to the clipboard."""
        figure = Figure(
            data.get_selected_style_params(),
            data,
            figure_settings=data.get_figure_settings(),
        )
        dpi = figure.get_dpi()
        figure.set_size_inches(width / dpi, height / dpi)
        svg, png = io.BytesIO(), io.BytesIO()
        figure.savefig(svg, format="svg", bbox_inches=None)
        figure.savefig(png, format="png", dpi=2 * dpi, bbox_inches=None)
        figure.detach()
        images = (("image/svg+xml", svg), ("image/png", png))
        Gdk.Display.get_default().get_clipboard().set_content(
            Gdk.ContentProvider.new_union([
                Gdk.ContentProvider.new_for_bytes(
                    mime_type,
                    GLib.Bytes.new(image.getvalue()),
                )
                for mime_type, image in images
            ]),
        )

    def _on_export_figure_request(
        self,
        file: Gio.File,
        settings: Gio.Settings,
        data: Graphs.Data,
    ) -> None:
        with gio_pyio.open(file, "wb") as file_like:
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
        item: Graphs.EquationItem,
        xstart: float,
        xstop: float,
    ) -> None:
        domain = sympy.Interval(xstart, xstop)
        return singularities(ast.sympify_item(item), x, domain)

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
        simplified = sympy.simplify(ast.sympify(expression))
        if not ast.is_supported(simplified):
            return None
        return str(simplified)
