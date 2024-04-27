# SPDX-License-Identifier: GPL-3.0-or-later
"""Python Helper - Python part."""
from gi.repository import Graphs

from graphs import curve_fitting, edit_item, figure_settings, utilities

_REQUEST_NAMES = (
    "python_method_request",
    "figure_settings_dialog_request",
    "edit_item_dialog_request",
    "curve_fitting_dialog_request",
    "validate_input_request",
)


class PythonHelper(Graphs.PythonHelper):
    """Python helper for python only calls."""

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)

        for request_name in _REQUEST_NAMES:
            self.connect(
                request_name,
                getattr(self, "_on_" + request_name),
            )

    @staticmethod
    def _on_python_method_request(self, obj, method: str) -> None:
        getattr(obj, method)()

    @staticmethod
    def _on_figure_settings_dialog_request(self) -> None:
        return figure_settings.FigureSettingsDialog(self.props.application)

    @staticmethod
    def _on_edit_item_dialog_request(self, item) -> None:
        return edit_item.EditItemDialog(self.props.application, item)

    @staticmethod
    def _on_curve_fitting_dialog_request(self, item) -> None:
        return curve_fitting.CurveFittingDialog(self.props.application, item)

    @staticmethod
    def _on_validate_input_request(self, string: str) -> bool:
        return utilities.string_to_float(string) is not None
