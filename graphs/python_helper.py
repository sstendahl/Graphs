# SPDX-License-Identifier: GPL-3.0-or-later
"""Python Helper - Python part."""
from gi.repository import Gio, Graphs

from graphs import (
    curve_fitting,
    export_items,
    file_io,
    operations,
    utilities,
)
from graphs.figure import Figure
from graphs.item import EquationItem, GeneratedDataItem
from graphs.style_editor import PythonStyleEditor
from graphs.window import PythonWindow

import sympy

_REQUESTS = (
    "add-equation",
    "create-style-editor",
    "create-window",
    "curve-fitting-dialog",
    "export-figure",
    "export-items",
    "generate-data",
    "perform-operation",
    "python-method",
    "simplify-equation",
    "validate-equation",
)


class PythonHelper(Graphs.PythonHelper):
    """Python helper for python only calls."""

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)

        self.set_instance(self)

        for request in _REQUESTS:
            request = request + "-request"
            self.connect(
                request,
                getattr(self, "_on_" + request.replace("-", "_")),
            )

    @staticmethod
    def _on_add_equation_request(
        self,
        window: Graphs.Window,
        equation: str,
        name: str,
    ) -> EquationItem:
        if name == "":
            name = f"Y = {equation}"
        return EquationItem.new(
            window.get_data().get_selected_style_params(),
            equation,
            name=name,
        )

    @staticmethod
    def _on_create_style_editor_request(self) -> Graphs.StyleEditor:
        return PythonStyleEditor(self.props.application)

    @staticmethod
    def _on_create_window_request(self) -> Graphs.Window:
        return PythonWindow(self.props.application)

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
            figure = Figure(data.get_selected_style_params(), data)
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
    def _on_generate_data_request(
        self,
        window: Graphs.Window,
        name: str,
    ) -> GeneratedDataItem:
        settings = Graphs.Application.get_settings_child("generate-data")
        equation = settings.get_string("equation")
        if name == "":
            name = f"Y = {settings.get_string('equation')}"
        return GeneratedDataItem.new(
            window.get_data().get_selected_style_params(),
            equation,
            settings.get_string("xstart"),
            settings.get_string("xstop"),
            settings.get_int("steps"),
            settings.get_int("scale"),
            name=name,
        )

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
    def _on_simplify_equation_request(self, equation: str) -> str:
        return str(sympy.simplify(equation))

    @staticmethod
    def _on_validate_equation_request(self, equation: str) -> bool:
        return utilities.equation_to_data(equation, steps=10)[0] is not None
