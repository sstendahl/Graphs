# SPDX-License-Identifier: GPL-3.0-or-later
"""Data management module."""
import copy
import logging
import math
from collections import OrderedDict
from collections.abc import Iterator
from gettext import gettext as _
from operator import itemgetter
from typing import Tuple

from gi.repository import Gio, Graphs, Gtk

from graphs import item, misc, project, style_io, utilities
from graphs.misc import ChangeType

from matplotlib import RcParams

import numpy

import sympy
from sympy.calculus.singularities import singularities

_FIGURE_SETTINGS_HISTORY_IGNORELIST = misc.LIMITS + [
    "min-selected",
    "max-selected",
]


class Data(Graphs.Data):
    """Class for managing data."""

    __gtype_name__ = "GraphsPythonData"

    def __init__(self):
        self._selected_style_params = None, {}
        super().__init__()
        self.connect("load-request", self._on_load_request)
        self.connect("position-changed", self._on_position_changed)
        self.connect("item-changed", self._on_item_changed)
        self.connect("item-added", self._on_item_added)
        self.connect("item-removed", self._on_item_removed)
        self.connect(
            "figure-settings-changed",
            self._on_figure_settings_changed,
        )
        self.connect(
            "add-history-state-request",
            self._on_add_history_state_request,
        )

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

    def get_old_selected_style_params(self) -> Tuple[RcParams, dict]:
        """Get the old selected style properties."""
        return self._old_style_params

    def get_selected_style_params(self) -> Tuple[RcParams, dict]:
        """Get the selected style properties."""
        return self._selected_style_params

    def _update_selected_style(self) -> None:
        figure_settings = self.props.figure_settings
        style_manager = Graphs.StyleManager.get_instance()
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

                        style_params, graphs_params = style_io.parse(
                            style.get_file(),
                            validate,
                        )
                        self._selected_style_params = \
                            style_params, graphs_params

                        self.set_color_cycle(
                            style_params["axes.prop_cycle"].by_key()["color"],
                        )
                        return
                    except (ValueError, SyntaxError, AttributeError):
                        error_msg = _(
                            "Could not parse style {stylename}, loading "
                            "system preferred style",
                        ).format(stylename=stylename)
                    break
            error_msg = _(
                "Style {stylename} does not exist, "
                "loading system preferred style",
            ).format(stylename=stylename)

        if error_msg is not None:
            figure_settings.set_use_custom_style(False)
            logging.warning(error_msg)

        self._old_style_params = self._selected_style_params
        self._selected_style_params = style_manager.get_system_style_params()
        color_cycle = self._selected_style_params[0]["axes.prop_cycle"]
        self.set_color_cycle(color_cycle.by_key()["color"])

    def _init_history_states(self) -> None:
        limits = self.props.figure_settings.get_limits()
        self._history_states = [([], limits)]
        self._history_pos = -1
        self._view_history_states = [limits]
        self._view_history_pos = -1
        self._set_data_copy()

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
    def _on_item_removed(self, item_: Graphs.Item, index: int) -> None:
        self._current_batch.append((
            ChangeType.ITEM_REMOVED.value,
            (index, item_.to_dict()),
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

    @staticmethod
    def _on_figure_settings_changed(self, prop: str) -> None:
        if prop in _FIGURE_SETTINGS_HISTORY_IGNORELIST:
            return
        self._current_batch.append((
            ChangeType.FIGURE_SETTINGS_CHANGED.value,
            (
                prop,
                copy.deepcopy(self._figure_settings_copy[prop]),
                copy.deepcopy(self.props.figure_settings.get_property(prop)),
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

    def _collapse_current_batch(self) -> None:
        """
        Collapse transitive changes within the current history batch.

        This method reduces redundant "change" entries in the current history
        batch:
        - Multiple consecutive item and figure settings changes to the same
          property are collapsed into a single change.
        - If a collapsed change would be meaningless (the original old value
          is equal to the most recent new value), that change is dropped.
        - If the batch contains structural changes like items added or removed,
          the method aborts and leaves the batch unchanged.
        """
        if not self._current_batch:
            # Nothing to collapse
            return

        collapsed = OrderedDict()

        for change_type, data in self._current_batch:
            match ChangeType(change_type):
                case ChangeType.ITEM_PROPERTY_CHANGED:
                    index, prop, old_value, new_value = data
                    key = (change_type, index, prop)

                    if key not in collapsed:
                        collapsed[key] = (change_type, data)
                    else:
                        first_old = collapsed[key][1][2]
                        if first_old == new_value:
                            collapsed.pop(key)
                        else:
                            collapsed[key] = (
                                ChangeType.ITEM_PROPERTY_CHANGED.value,
                                (index, prop, first_old, new_value),
                            )

                case ChangeType.FIGURE_SETTINGS_CHANGED:
                    prop, old_value, new_value = data
                    key = (change_type, prop)

                    if key not in collapsed:
                        collapsed[key] = (change_type, data)
                    else:
                        first_old = collapsed[key][1][1]
                        if first_old == new_value:
                            collapsed.pop(key)
                        else:
                            collapsed[key] = (
                                ChangeType.FIGURE_SETTINGS_CHANGED.value,
                                (prop, first_old, new_value),
                            )

                case _:
                    # On any other change such as items added or removed we
                    # abort collapsing
                    return

        self._current_batch = list(collapsed.values())

    @staticmethod
    def _on_add_history_state_request(
        self,
        limits: misc.Limits,
        l: int,
    ) -> bool:
        """Add a state to the clipboard."""
        self._collapse_current_batch()
        if not self._current_batch:
            # Nothing to add
            return False
        if self._history_pos != -1:
            self._history_states = self._history_states[:self._history_pos + 1]
        self._history_pos = -1
        self._history_states.append(
            (self._current_batch, self.get_figure_settings().get_limits()),
        )
        if l > 0:
            assert l == 8
            old_state = self._history_states[-2][1]
            for index in range(8):
                old_state[index] = limits[index]
        # Keep history states length limited to 100 spots
        if len(self._history_states) > 101:
            self._history_states = self._history_states[1:]
        self._set_data_copy()
        return True

    def _undo(self) -> None:
        """Undo the latest change that was added to the clipboard."""
        if not self.props.can_undo:
            return
        batch = self._history_states[self._history_pos][0]
        self._history_pos -= 1
        selected = Gtk.Bitset.new_empty()
        mask = Gtk.Bitset.new_empty()
        for change_type, change in reversed(batch):
            match ChangeType(change_type):
                case ChangeType.ITEM_PROPERTY_CHANGED:
                    index, prop, value = itemgetter(0, 1, 2)(change)
                    if prop == "selected":
                        mask.add(index)
                        if value:
                            selected.add(index)
                    else:
                        self[index].set_property(prop, value)
                case ChangeType.ITEM_ADDED:
                    self._remove_item(self.get_n_items() - 1)
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
        self.set_selection(selected, mask)
        self.get_figure_settings().set_limits(
            self._history_states[self._history_pos][1],
        )
        self.props.can_redo = True
        self.props.can_undo = \
            abs(self._history_pos) < len(self._history_states)
        self._set_data_copy()

    def _redo(self) -> None:
        """Redo the latest change that was added to the clipboard."""
        if not self.props.can_redo:
            return
        self._history_pos += 1
        state = self._history_states[self._history_pos]
        selected = Gtk.Bitset.new_empty()
        mask = Gtk.Bitset.new_empty()
        for change_type, change in state[0]:
            match ChangeType(change_type):
                case ChangeType.ITEM_PROPERTY_CHANGED:
                    index, prop, value = itemgetter(0, 1, 3)(change)
                    if prop == "selected":
                        mask.add(index)
                        if value:
                            selected.add(index)
                    else:
                        self[index].set_property(prop, value)
                case ChangeType.ITEM_ADDED:
                    self._add_item(
                        item.new_from_dict(copy.deepcopy(change)),
                        -1,
                        True,
                    )
                case ChangeType.ITEM_REMOVED:
                    self._remove_item(change[0])
                case ChangeType.ITEMS_SWAPPED:
                    self.change_position(change[1], change[0])
                case ChangeType.FIGURE_SETTINGS_CHANGED:
                    self.props.figure_settings.set_property(
                        change[0],
                        change[2],
                    )
        self.set_selection(selected, mask)
        self.get_figure_settings().set_limits(state[1])
        self.props.can_redo = self._history_pos < -1
        self.props.can_undo = True
        self._set_data_copy()

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

                xdata, ydata = copy.deepcopy(item_.props.data)
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

            x = sympy.Symbol("x")
            equation = utilities.preprocess(item_.equation.lower())
            expr = sympy.sympify(equation)
            domain = sympy.Interval(*x_limits)
            has_singularities = singularities(expr, x, domain)
            yaxis[1] = True
            ydata = utilities.equation_to_data(item_.equation, x_limits)[1]

            ydata_arr = numpy.asarray(ydata)
            if has_singularities:
                # Don't take negative values into account for log scaling
                if yaxis[4] in (1, 2):
                    ydata_arr = ydata_arr[ydata_arr > 0]

                y_min, y_max = ydata_arr.min(), ydata_arr.max()
                lower_bound = utilities.get_value_at_fraction(
                    0.05, y_min, y_max, yaxis[4],
                )
                upper_bound = utilities.get_value_at_fraction(
                    0.95, y_min, y_max, yaxis[4],
                )
                ydata_arr = ydata_arr[
                    (ydata_arr >= lower_bound) & (ydata_arr <= upper_bound)
                ]

            min_max = self._get_min_max_from_array(
                ydata_arr,
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
                max_all += padding_factor * span

                # For inverse scale, calculate padding using a factor
                min_all = (
                    min_all - padding_factor * span if scale != 4 else min_all
                    * 0.99
                )
            else:  # Use different scaling type for logarithmic scale
                log_min = numpy.log10(min_all) if min_all > 0 else 0
                log_max = numpy.log10(max_all) if max_all > 0 else 0
                log_span = log_max - log_min

                padding_factor = 0.05 if count % 2 else 0.015
                log_min -= padding_factor * log_span
                log_max += padding_factor * log_span
                min_all = 10 ** log_min
                max_all = 10 ** log_max
            figure_settings.set_property(f"min_{direction}", min_all)
            figure_settings.set_property(f"max_{direction}", max_all)

    def get_project_dict(self) -> dict:
        """Convert data to dict."""
        figure_settings = self.get_figure_settings()
        return {
            "version": self.get_version(),
            "data": [item_.to_dict() for item_ in self],
            "figure-settings": {
                key.replace("_", "-"): figure_settings.get_property(key)
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
        self.set_figure_settings(
            Graphs.FigureSettings(
                **{
                    key.replace("-", "_"): value
                    for (key, value) in project_dict["figure-settings"].items()
                },
            ),
        )
        self.set_items([item.new_from_dict(d) for d in project_dict["data"]])

        # Set clipboard
        self._set_data_copy()
        self._history_states = project_dict["history-states"]
        self._history_pos = project_dict["history-position"]
        self._view_history_states = project_dict["view-history-states"]
        self._view_history_pos = project_dict["view-history-position"]

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
    def _on_load_request(
        self,
        file: Gio.File,
        parse_flags: Graphs.ProjectParseFlags,
    ) -> str:
        try:
            project_dict = project.read_project_file(file, parse_flags)
        except project.ProjectParseError as error:
            if error.log:
                logging.exception(error)
            return error.message
        current_data = self.get_project_dict()
        try:
            self.load_from_project_dict(project_dict)
        except Exception:
            self.load_from_project_dict(current_data)
            msg = _("Failed to load project")
            logging.exception(msg)
            return msg
        return ""
