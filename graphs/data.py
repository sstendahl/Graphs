# SPDX-License-Identifier: GPL-3.0-or-later
"""Data management module."""
import copy
import logging
import math
from collections import OrderedDict
from collections.abc import Iterator
from gettext import gettext as _
from operator import itemgetter

from gi.repository import Gio, Graphs, Gtk

from graphs import misc, project, style_io, utilities
from graphs.item import ItemFactory

from matplotlib import RcParams

import numexpr

import numpy

import sympy
from sympy.calculus.singularities import singularities

_FIGURE_SETTINGS_HISTORY_IGNORELIST = misc.LIMITS + [
    "min-selected",
    "max-selected",
]

LOG_SCALES = {1, 2}
NONZERO_SCALES = {1, 2, 4}


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
        for i in range(self.get_n_items()):
            yield self.get_item(i)

    def __getitem__(self, pos: int):
        """Magic alias for retrieving items."""
        return self.get_item(pos)

    def get_old_selected_style_params(self) -> tuple[RcParams, dict]:
        """Get the old selected style properties."""
        return self._old_style_params

    def get_selected_style_params(self) -> tuple[RcParams, dict]:
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
                        self.set_errbar_color_cycle(
                            graphs_params["errorbar.color_cycle"].by_key()
                            ["color"],
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
        graphs_params = self._selected_style_params[1]
        self.set_errbar_color_cycle(
            graphs_params["errorbar.color_cycle"].by_key()["color"],
        )

    def _init_history_states(self) -> None:
        limits = self.props.figure_settings.get_limits().values()
        self._history_states = [([], limits)]
        self._history_pos = -1
        self._set_data_copy()

    @staticmethod
    def _on_position_changed(self, index1: int, index2: int) -> None:
        """Change item position of index2 to that of index1."""
        self._current_batch.append((
            Graphs.ChangeType.ITEMS_SWAPPED,
            (index2, index1),
        ))

    @staticmethod
    def _on_item_added(self, item: Graphs.Item) -> None:
        self._current_batch.append((
            Graphs.ChangeType.ITEM_ADDED,
            copy.deepcopy(item.to_dict()),
        ))

    @staticmethod
    def _on_item_removed(self, item: Graphs.Item, index: int) -> None:
        self._current_batch.append((
            Graphs.ChangeType.ITEM_REMOVED,
            (index, item.to_dict()),
        ))

    @staticmethod
    def _on_item_changed(self, item: Graphs.Item, prop: str) -> None:
        index = self.index(item)
        self._current_batch.append((
            Graphs.ChangeType.ITEM_PROPERTY_CHANGED,
            (
                index,
                prop,
                copy.deepcopy(self._data_copy[index][prop]),
                copy.deepcopy(item.get_property(prop)),
            ),
        ))

    @staticmethod
    def _on_figure_settings_changed(self, prop: str) -> None:
        if prop in _FIGURE_SETTINGS_HISTORY_IGNORELIST:
            return
        self._current_batch.append((
            Graphs.ChangeType.FIGURE_SETTINGS_CHANGED,
            (
                prop,
                copy.deepcopy(self._figure_settings_copy[prop]),
                copy.deepcopy(self.props.figure_settings.get_property(prop)),
            ),
        ))

    def _set_data_copy(self) -> None:
        """Set a deep copy for the data."""
        self._current_batch: list = []
        self._data_copy = copy.deepcopy([item.to_dict() for item in self])
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
            match change_type:
                case Graphs.ChangeType.ITEM_PROPERTY_CHANGED:
                    index, prop, _old_value, new_value = data
                    key = (change_type, index, prop)

                    if key not in collapsed:
                        collapsed[key] = (change_type, data)
                    else:
                        first_old = collapsed[key][1][2]
                        if first_old == new_value:
                            collapsed.pop(key)
                        else:
                            collapsed[key] = (
                                Graphs.ChangeType.ITEM_PROPERTY_CHANGED,
                                (index, prop, first_old, new_value),
                            )

                case Graphs.ChangeType.FIGURE_SETTINGS_CHANGED:
                    prop, _old_value, new_value = data
                    key = (change_type, prop)

                    if key not in collapsed:
                        collapsed[key] = (change_type, data)
                    else:
                        first_old = collapsed[key][1][1]
                        if first_old == new_value:
                            collapsed.pop(key)
                        else:
                            collapsed[key] = (
                                Graphs.ChangeType.FIGURE_SETTINGS_CHANGED,
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
        limits = self.get_figure_settings().get_limits().values()
        self._history_states.append((self._current_batch, limits))
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
            match change_type:
                case Graphs.ChangeType.ITEM_PROPERTY_CHANGED:
                    index, prop, value = itemgetter(0, 1, 2)(change)
                    if prop == "selected":
                        mask.add(index)
                        if value:
                            selected.add(index)
                    else:
                        self[index].set_property(prop, value)
                case Graphs.ChangeType.ITEM_ADDED:
                    self._remove_item(self.get_n_items() - 1)
                case Graphs.ChangeType.ITEM_REMOVED:
                    self._insert_item(
                        ItemFactory.new_from_dict(copy.deepcopy(change[1])),
                        change[0],
                    )
                case Graphs.ChangeType.ITEMS_SWAPPED:
                    self.change_position(change[0], change[1])
                case Graphs.ChangeType.FIGURE_SETTINGS_CHANGED:
                    self.props.figure_settings.set_property(
                        change[0],
                        change[1],
                    )
        self.set_selection(selected, mask)
        limits = Graphs.Limits(self._history_states[self._history_pos][1])
        self.get_figure_settings().set_limits(limits)
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
            match change_type:
                case Graphs.ChangeType.ITEM_PROPERTY_CHANGED:
                    index, prop, value = itemgetter(0, 1, 3)(change)
                    if prop == "selected":
                        mask.add(index)
                        if value:
                            selected.add(index)
                    else:
                        self[index].set_property(prop, value)
                case Graphs.ChangeType.ITEM_ADDED:
                    change = copy.deepcopy(change)
                    self._add_item(ItemFactory.new_from_dict(change))
                case Graphs.ChangeType.ITEM_REMOVED:
                    self._remove_item(change[0])
                case Graphs.ChangeType.ITEMS_SWAPPED:
                    self.change_position(change[1], change[0])
                case Graphs.ChangeType.FIGURE_SETTINGS_CHANGED:
                    self.props.figure_settings.set_property(
                        change[0],
                        change[2],
                    )
        self.set_selection(selected, mask)
        self.get_figure_settings().set_limits(Graphs.Limits(state[1]))
        self.props.can_redo = self._history_pos < -1
        self.props.can_undo = True
        self._set_data_copy()

    def _optimize_limits(self) -> None:
        """Optimize the limits of the canvas to the data class."""
        figure_settings = self.get_figure_settings()

        axes = [[
            direction,
            False,
            figure_settings.get_property(f"min_{direction}"),
            figure_settings.get_property(f"max_{direction}"),
            figure_settings.get_property(f"{direction}_scale"),
            None,
        ] for direction in ("bottom", "left", "top", "right")]

        equation_items = []
        hide_unselected = figure_settings.get_hide_unselected()

        for item in self:
            if not isinstance(item, (Graphs.DataItem, Graphs.EquationItem)):
                continue

            if not item.get_selected() and hide_unselected:
                continue

            if isinstance(item, Graphs.EquationItem):
                equation_items.append(item)
                continue

            indices = (item.get_xposition() * 2, 1 + item.get_yposition() * 2)
            for index, xydata in zip(indices, item.get_xydata()):
                axis = axes[index]

                xydata = numpy.asarray(xydata)
                xydata = xydata[numpy.isfinite(xydata)]

                if xydata.size == 0:
                    continue

                if axis[4] in NONZERO_SCALES:
                    nonzero = xydata[xydata != 0]
                    min_value = nonzero.min() if nonzero.size else xydata.min()
                else:
                    min_value = xydata.min()
                max_value = xydata.max()

                if axis[1]:
                    axis[2] = min(axis[2], min_value)
                    axis[3] = max(axis[3], max_value)
                else:
                    axis[2] = min_value
                    axis[3] = max_value
                    axis[1] = True

        for item in equation_items:
            xindex = item.get_xposition() * 2
            xaxis = axes[xindex]
            yaxis = axes[1 + item.get_yposition() * 2]
            x_limits = [xaxis[2], xaxis[3]]
            yscale = yaxis[4]

            equation = item.get_preprocessed_equation()
            expr = sympy.sympify(equation)
            domain = sympy.Interval(*x_limits)
            has_singularities = singularities(expr, misc.X, domain)

            if xaxis[5] is None:
                xscale = xaxis[4]
                xaxis[5] = utilities.create_equidistant_xdata(x_limits, xscale)
            ydata = numexpr.evaluate(equation, local_dict={"x": xaxis[5]})
            ydata = ydata[numpy.isfinite(ydata)]

            if has_singularities:
                # Don't take negative values into account for log scaling
                if yscale in LOG_SCALES:
                    ydata = ydata[ydata > 0]

                y_min, y_max = ydata.min(), ydata.max()
                lower_bound = Graphs.get_value_at_fraction(
                    0.05,
                    y_min,
                    y_max,
                    yscale,
                )
                upper_bound = Graphs.get_value_at_fraction(
                    0.95,
                    y_min,
                    y_max,
                    yscale,
                )
                ydata = ydata.clip(lower_bound, upper_bound)

            if ydata.size == 0:
                continue

            if yscale in NONZERO_SCALES:
                nonzero = ydata[ydata != 0]
                min_value = nonzero.min() if nonzero.size else ydata.min()
            else:
                min_value = ydata.min()
            max_value = ydata.max()

            if yaxis[1]:
                yaxis[2] = min(yaxis[2], min_value)
                yaxis[3] = max(yaxis[3], max_value)
            else:
                yaxis[2] = min_value
                yaxis[3] = max_value
                yaxis[1] = True

        for count, (direction, used, min_all, max_all, scale, _x) in \
                enumerate(axes):
            if not used:
                continue

            # 0.05 padding on y-axis, 0.015 padding on x-axis
            padding_factor = 0.05 if count % 2 else 0.015

            if scale not in LOG_SCALES:  # For non-logarithmic scales
                span = max_all - min_all
                max_all += padding_factor * span

                # For inverse scale, calculate padding using a factor
                if scale == 4:
                    min_all *= 0.99
                else:
                    min_all -= padding_factor * span
            else:  # Use different scaling type for logarithmic scale
                log_min = numpy.log10(min_all) if min_all > 0 else 0
                log_max = numpy.log10(max_all) if max_all > 0 else 0
                log_span = log_max - log_min

                log_min -= padding_factor * log_span
                log_max += padding_factor * log_span
                min_all = 10**log_min
                max_all = 10**log_max
            figure_settings.set_property(f"min_{direction}", min_all)
            figure_settings.set_property(f"max_{direction}", max_all)

    def get_project_dict(self) -> dict:
        """Convert data to dict."""
        figure_settings = self.get_figure_settings()
        view_pos, view_states = self.get_view_history()
        return {
            "version": self.get_version(),
            "data": [item.to_dict() for item in self],
            "figure-settings": {
                key.replace("_", "-"): figure_settings.get_property(key)
                for key in dir(figure_settings.props)
            },
            "history-states": self._history_states,
            "history-position": self._history_pos,
            "view-history-states": [lims.values() for lims in view_states],
            "view-history-position": view_pos,
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
        items = [ItemFactory.new_from_dict(d) for d in project_dict["data"]]
        self.set_items(items)

        # Set clipboard
        self._set_data_copy()
        self._history_states = project_dict["history-states"]
        self._history_pos = project_dict["history-position"]
        view_states = project_dict["view-history-states"]
        limits = list(map(Graphs.Limits.new, view_states))
        self.set_view_history(project_dict["view-history-position"], limits)

        # Set clipboard/view buttons
        self.props.can_undo = \
            abs(self._history_pos) < len(self._history_states)
        self.props.can_redo = self._history_pos < -1

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
