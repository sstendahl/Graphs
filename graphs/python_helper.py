# SPDX-License-Identifier: GPL-3.0-or-later
"""Python Helper - Python part."""
from gi.repository import Gio, Graphs

from graphs import (
    curve_fitting,
    edit_item,
    export_items,
    file_import,
    utilities,
)

_REQUEST_NAMES = (
    "python_method_request",
    "edit_item_dialog_request",
    "curve_fitting_dialog_request",
    "validate_input_request",
    "import_from_files_request",
    "export_items_request",
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
    def _on_edit_item_dialog_request(self, item) -> None:
        return edit_item.EditItemDialog(self.props.application, item)

    @staticmethod
    def _on_curve_fitting_dialog_request(self, item) -> None:
        return curve_fitting.CurveFittingDialog(self.props.application, item)

    @staticmethod
    def _on_validate_input_request(self, string: str) -> bool:
        return utilities.string_to_float(string) is not None

    @staticmethod
    def _on_import_from_files_request(self, files: Gio.ListModel) -> None:
        return file_import.import_from_files(self.props.application, files)

    @staticmethod
    def _on_export_items_request(
        self,
        mode: str,
        file: Gio.File,
        items: list[Graphs.Item],
        _n_items: int,
    ) -> None:
        return export_items.export_items(mode, file, items)
