# SPDX-License-Identifier: GPL-3.0-or-later
"""UI representation of an Item."""
from gi.repository import Graphs

from graphs.curve_fitting import CurveFittingDialog
from graphs.edit_item import EditItemDialog


class ItemBox(Graphs.ItemBox):
    """UI representation of an Item."""

    __gtype_name__ = "GraphsPythonItemBox"

    def __init__(self, application, item, index):
        super().__init__(
            application=application,
            item=item,
            index=index,
        )
        self.setup(len(application.get_data()))
        self.connect("edit-request", self._on_edit_request)
        self.connect("curve-fitting-request", self._on_curve_fitting_request)

    @staticmethod
    def _on_edit_request(self) -> None:
        """Show Edit Item Dialog."""
        EditItemDialog(self.props.application, self.props.item)

    @staticmethod
    def _on_curve_fitting_request(self) -> None:
        """Open Curve Fitting dialog."""
        CurveFittingDialog(self.props.application, self.props.item)
