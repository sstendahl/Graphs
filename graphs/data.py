# SPDX-License-Identifier: GPL-3.0-or-later
"""Data management module."""
import copy
import enum
import logging
import math
from collections.abc import Iterator
from gettext import gettext as _

from gi.repository import GObject, Gio, Graphs

from graphs import item, misc, project, style_io, utilities

from matplotlib import RcParams

import numpy

_FIGURE_SETTINGS_HISTORY_IGNORELIST = misc.LIMITS + [
    "min_selected",
    "max_selected",
]


class ChangeType(enum.Enum):
    """Enum for handling changetypes."""

    ITEM_PROPERTY_CHANGED = 0
    ITEM_ADDED = 1
    ITEM_REMOVED = 2
    ITEMS_SWAPPED = 3
    FIGURE_SETTINGS_CHANGED = 4


class Data(Graphs.Data):
    """Class for managing data."""

    __gtype_name__ = "GraphsPythonData"

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)
        self.connect("python_method_request", self._on_python_method_request)
        self._selected_style_params = None
        self.setup()
        limits = self.props.figure_settings.get_limits()
        self._history_states = [([], limits)]
        self._history_pos = -1
        self._view_history_states = [limits]
        self._view_history_pos = -1
        self._set_data_copy()
        self.props.figure_settings.connect(
            "notify",
            self._on_figure_settings_change,
        )
        self.connect("load_request", self._on_load_request)
        self.connect("position_changed", self._on_position_changed)
        self.connect("item_changed", self._on_item_changed)
        self.connect("item_added", self._on_item_added)
        self.connect("item_deleted", self._on_item_deleted)

    @staticmethod
    def _on_python_method_request(self, method: str) -> None:
        getattr(self, method)()

    def __len__(self) -> int:
        """Magic alias for `get_n_items()`."""
        return self.get_n_items()

    def __iter__(self) -> Iterator[Graphs.Item]:
        """Iterate over items."""
        iterator = self.iterator_wrapper()
        while True:
            item_ = iterator.next()
            if item_ is None:
                return
            yield item_

    def __getitem__(self, pos: int):
        """Magic alias for retrieving items."""
        return self.get_item(pos)

    def get_old_selected_style_params(self) -> RcParams:
        """Get the old selected style properties."""
        return self._old_style_params

    def get_selected_style_params(self) -> RcParams:
        """Get the selected style properties."""
        return self._selected_style_params

    def _update_selected_style(self) -> None:
        figure_settings = self.props.figure_settings
        style_manager = self.props.application.get_figure_style_manager()
        error_msg = None
        if figure_settings.get_use_custom_style():
            stylename = figure_settings.get_custom_style()
            for style in self.props.style_selection_model.get_model():
                if stylename == style.get_name():
                    try:
                        validate = None
                        if style.get_mutable():
                            validate = style_manager.get_system_style_params()
                        self._old_style_params = self._selected_style_params
                        style_params = style_io.parse(
                            style.get_file(),
                            validate,
                        )[0]
                        self._selected_style_params = style_params
                        self.set_color_cycle(
                            style_params["axes.prop_cycle"].by_key()["color"],
                        )
                        return
                    except (ValueError, SyntaxError, AttributeError):
                        error_msg = _(
                            f"Could not parse {stylename}, loading "
                            "system preferred style",
                        ).format(stylename=stylename)
                    break
            error_msg = _(
                f"Plot style {stylename} does not exist "
                "loading system preferred",
            ).format(stylename=stylename)
        if error_msg is not None:
            figure_settings.set_use_custom_style(False)
            logging.warning(error_msg)
        self._old_style_params = self._selected_style_params
        self._selected_style_params = style_manager.get_system_style_params()
        self.set_color_cycle(
            self._selected_style_params["axes.prop_cycle"].by_key()["color"],
        )

    @staticmethod
    def _on_position_changed(self, index1: int, index2: int) -> None:
        """Change item position of index2 to that of index1."""
        self._current_batch.append((
            ChangeType.ITEMS_SWAPPED.value,
            (index2, index1),
        ))

    @staticmethod
    def _on_item_added(self, item_: Graphs.Item) -> None:
        self._current_batch.append((
            ChangeType.ITEM_ADDED.value,
            copy.deepcopy(item_.to_dict()),
        ))

    @staticmethod
    def _on_item_deleted(self, item_: Graphs.Item) -> None:
        self._current_batch.append((
            ChangeType.ITEM_REMOVED.value,
            (self.index(item_), item_.to_dict()),
        ))

    @staticmethod
    def _on_item_changed(self, item_: Graphs.Item, prop: str) -> None:
        index = self.index(item_)
        self._current_batch.append((
            ChangeType.ITEM_PROPERTY_CHANGED.value,
            (
                index,
                prop,
                copy.deepcopy(self._data_copy[index][prop]),
                copy.deepcopy(item_.get_property(prop)),
            ),
        ))

    def _on_figure_settings_change(
        self,
        figure_settings: Graphs.FigureSettings,
        param: GObject.ParamSpec,
    ) -> None:
        if param.name in _FIGURE_SETTINGS_HISTORY_IGNORELIST:
            return
        self._current_batch.append((
            ChangeType.FIGURE_SETTINGS_CHANGED.value,
            (
                param.name,
                copy.deepcopy(self._figure_settings_copy[param.name]),
                copy.deepcopy(figure_settings.get_property(param.name)),
            ),
        ))

    def _set_data_copy(self) -> None:
        """Set a deep copy for the data."""
        self._current_batch: list = []
        self._data_copy = copy.deepcopy([item_.to_dict() for item_ in self])
        self._figure_settings_copy = copy.deepcopy({
            prop.replace("_", "-"):
            self.props.figure_settings.get_property(prop)
            for prop in dir(self.props.figure_settings.props)
        })

    def add_history_state_with_limits(self, old_limits: misc.Limits) -> None:
        """Add a state to the clipboard with old_limits set."""
        self._add_history_state(old_limits)

    def _add_history_state(self, old_limits: misc.Limits = None) -> None:
        """Add a state to the clipboard."""
        if not self._current_batch:
            return
        if self._history_pos != -1:
            self._history_states = self._history_states[:self._history_pos + 1]
        self._history_pos = -1
        self._history_states.append(
            (self._current_batch, self.get_figure_settings().get_limits()),
        )
        if old_limits is not None:
            old_state = self._history_states[-2][1]
            for index in range(8):
                old_state[index] = old_limits[index]
        self.props.can_redo = False
        self.props.can_undo = True
        # Keep history states length limited to 100 spots
        if len(self._history_states) > 101:
            self._history_states = self._history_states[1:]
        self._set_data_copy()
        self.props.unsaved = True

    def _undo(self) -> None:
        """Undo the latest change that was added to the clipboard."""
        if not self.props.can_undo:
            return
        batch = self._history_states[self._history_pos][0]
        self._history_pos -= 1
        for change_type, change in reversed(batch):
            match ChangeType(change_type):
                case ChangeType.ITEM_PROPERTY_CHANGED:
                    self[change[0]].set_property(change[1], change[2])
                case ChangeType.ITEM_ADDED:
                    self._remove_item(self.last())
                case ChangeType.ITEM_REMOVED:
                    self._add_item(
                        item.new_from_dict(copy.deepcopy(change[1])),
                        change[0],
                        True,
                    )
                case ChangeType.ITEMS_SWAPPED:
                    self.change_position(change[0], change[1])
                case ChangeType.FIGURE_SETTINGS_CHANGED:
                    self.props.figure_settings.set_property(
                        change[0],
                        change[1],
                    )
        self.get_figure_settings().set_limits(
            self._history_states[self._history_pos][1],
        )
        self.props.can_redo = True
        self.props.can_undo = \
            abs(self._history_pos) < len(self._history_states)
        self._set_data_copy()
        self._add_view_history_state()

    def _redo(self) -> None:
        """Redo the latest change that was added to the clipboard."""
        if not self.props.can_redo:
            return
        self._history_pos += 1
        state = self._history_states[self._history_pos]
        for change_type, change in state[0]:
            match ChangeType(change_type):
                case ChangeType.ITEM_PROPERTY_CHANGED:
                    self[change[0]].set_property(change[1], change[3])
                case ChangeType.ITEM_ADDED:
                    self._add_item(
                        item.new_from_dict(copy.deepcopy(change)),
                        -1,
                        True,
                    )
                case ChangeType.ITEM_REMOVED:
                    self._remove_item(self.get_item(change[0]))
                case ChangeType.ITEMS_SWAPPED:
                    self.change_position(change[1], change[0])
                case ChangeType.FIGURE_SETTINGS_CHANGED:
                    self.props.figure_settings.set_property(
                        change[0],
                        change[2],
                    )
        self.get_figure_settings().set_limits(state[1])
        self.props.can_redo = self._history_pos < -1
        self.props.can_undo = True
        self._set_data_copy()
        self._add_view_history_state()

    def _add_view_history_state(self) -> None:
        """Add the view to the view history."""
        limits = self.get_figure_settings().get_limits()
        if all(
            math.isclose(old, new) for old,
            new in zip(self._view_history_states[-1], limits)
        ):
            return
        # If a couple of redo's were performed previously, it deletes the
        # clipboard data that is located after the current clipboard
        # position and disables the redo button
        if self._view_history_pos != -1:
            self._view_history_states = \
                self._view_history_states[:self._view_history_pos + 1]
        if len(self._view_history_states) > 101:
            self._view_history_states = self._view_history_states[1::]
        self._view_history_pos = -1
        self._view_history_states.append(limits)
        self.props.can_view_back = True
        self.props.can_view_forward = False
        self.props.unsaved = True

    def _view_back(self) -> None:
        """Move the view to the previous value in the view history."""
        if not self.props.can_view_back:
            return
        self._view_history_pos -= 1
        self.get_figure_settings().set_limits(
            self._view_history_states[self._view_history_pos],
        )
        self.props.can_view_forward = True
        self.props.can_view_back = \
            abs(self._view_history_pos) < len(self._view_history_states)

    def _view_forward(self) -> None:
        """Move the view to the next value in the view history."""
        if not self.props.can_view_forward:
            return
        self._view_history_pos += 1
        self.get_figure_settings().set_limits(
            self._view_history_states[self._view_history_pos],
        )
        self.props.can_view_back = True
        self.props.can_view_forward = self._view_history_pos < -1

    @staticmethod
    def _get_min_max_from_array(xydata: list, scale: int) -> (float, float):
        try:
            xydata = xydata[numpy.isfinite(xydata)]
        except TypeError:
            return None
        nonzero_data = numpy.array([value for value in xydata if value != 0])
        min_value = nonzero_data.min() if scale in (1, 2, 4) \
            and len(nonzero_data) > 0 else xydata.min()
        max_value = xydata.max()
        return min_value, max_value

    def _optimize_limits(self) -> None:
        """Optimize the limits of the canvas to the data class."""
        figure_settings = self.get_figure_settings()
        axes = [[
            direction,
            False,
            [],
            [],
            figure_settings.get_property(f"{direction}_scale"),
        ] for direction in ("bottom", "left", "top", "right")]
        equation_items = []
        for item_ in self:
            if not isinstance(item_, (item.DataItem, item.EquationItem)) or (
                not item_.get_selected()
                and figure_settings.get_hide_unselected()
            ):
                continue
            if isinstance(item_, item.EquationItem):
                equation_items.append(item_)
                continue
            for index in \
                    item_.get_xposition() * 2, 1 + item_.get_yposition() * 2:
                axis = axes[index]
                axis[1] = True

                xdata = copy.deepcopy(item_.xdata)
                ydata = copy.deepcopy(item_.ydata)

                min_max = self._get_min_max_from_array(
                    numpy.asarray(ydata if index % 2 else xdata),
                    axis[4],
                )
                if min_max is None:
                    return
                min_value, max_value = min_max
                axis[2].append(min_value)
                axis[3].append(max_value)

        for item_ in equation_items:
            xaxis = axes[item_.get_xposition() * 2]
            yaxis = axes[1 + item_.get_yposition() * 2]
            if xaxis[1]:
                x_limits = [min(xaxis[2]), max(xaxis[3])]
            else:
                direction = xaxis[0]
                x_limits = [
                    figure_settings.get_property(f"min_{direction}"),
                    figure_settings.get_property(f"max_{direction}"),
                ]
            yaxis[1] = True

            ydata = utilities.equation_to_data(item_.equation, x_limits)[1]

            min_max = self._get_min_max_from_array(
                numpy.asarray(ydata),
                yaxis[4],
            )
            if min_max is None:
                return
            min_value, max_value = min_max
            yaxis[2].append(min_value)
            yaxis[3].append(max_value)

        for count, (direction, used, min_all, max_all, scale) in \
                enumerate(axes):
            if not used:
                continue
            min_all = min(min_all)
            max_all = max(max_all)
            if scale not in (1, 2):  # For non-logarithmic scales
                span = max_all - min_all
                # 0.05 padding on y-axis, 0.015 padding on x-axis
                padding_factor = 0.05 if count % 2 else 0.015
                if isinstance(item_, item.EquationItem) and not count % 2:
                    padding_factor = 0
                max_all += padding_factor * span

                # For inverse scale, calculate padding using a factor
                min_all = (
                    min_all - padding_factor * span if scale != 4 else min_all
                    * 0.99
                )
            else:  # Use different scaling type for logarithmic scale
                # Use padding factor of 2 for y-axis, 1.025 for x-axis
                padding_factor = 2 if count % 2 else 1.025
                if isinstance(item_, item.EquationItem) and not count % 2:
                    padding_factor = 0
                min_all *= 1 / padding_factor
                max_all *= padding_factor
            figure_settings.set_property(f"min_{direction}", min_all)
            figure_settings.set_property(f"max_{direction}", max_all)
        self._add_view_history_state()

    def get_project_dict(self) -> dict:
        """Convert data to dict."""
        figure_settings = self.get_figure_settings()
        return {
            "version": self.get_version(),
            "data": [item_.to_dict() for item_ in self],
            "figure-settings": {
                key: figure_settings.get_property(key)
                for key in dir(figure_settings.props)
            },
            "history-states": self._history_states,
            "history-position": self._history_pos,
            "view-history-states": self._view_history_states,
            "view-history-position": self._view_history_pos,
        }

    def load_from_project_dict(self, project_dict: dict) -> None:
        """Load data from dict."""
        # Load data
        figure_settings = self.get_figure_settings()
        for key, value in project_dict["figure-settings"].items():
            if figure_settings.get_property(key) != value:
                figure_settings.set_property(key, value)
        self.set_items([item.new_from_dict(d) for d in project_dict["data"]])

        # Set clipboard
        self._set_data_copy()
        self._history_states = project_dict["history-states"]
        self._history_pos = project_dict["history-position"]
        self._view_history_states = project_dict["view-history-states"]
        self._view_history_pos = project_dict["view-history-position"]
        self.unsaved = False

        # Set clipboard/view buttons
        self.props.can_undo = \
            abs(self._history_pos) < len(self._history_states)
        self.props.can_redo = self._history_pos < -1
        self.props.can_view_back = \
            abs(self._view_history_pos) < len(self._view_history_states)
        self.props.can_view_forward = self._view_history_pos < -1

    def _save(self) -> None:
        project.save_project_dict(self.props.file, self.get_project_dict())

    @staticmethod
    def _on_load_request(self, file: Gio.File) -> str:
        try:
            project_dict = project.read_project_file(file)
        except project.ProjectParseError as error:
            return error.message
        except Exception:
            msg = _("Failed to parse project file")
            logging.exception(msg)
            return msg
        current_data = self.get_project_dict()
        try:
            self.load_from_project_dict(project_dict)
        except Exception:
            self.load_from_project_dict(current_data)
            msg = _("Failed to load project")
            logging.exception(msg)
            return msg
        return ""
