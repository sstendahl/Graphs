# SPDX-License-Identifier: GPL-3.0-or-later
from matplotlib import pyplot


def optimize_limits(self):
    self.props.clipboard.clipboard[self.props.clipboard.clipboard_pos][
        "view"] = self.props.figure_settings.get_limits()
    axes = [
        [direction, False, []]
        for direction in ["bottom", "left", "top", "right"]
    ]
    for item in self.props.data.props.items:
        for index in item.xposition * 2, 1 + item.yposition * 2:
            axes[index][1] = True
            axes[index][2].append(item)

    for count, (direction, used, items) in enumerate(axes):
        if not used:
            continue
        scale = self.props.figure_settings.get_property(f"{direction}_scale")
        datalist = [item.ydata if count % 2 else item.xdata for item in items
                    if item.props.item_type == "Item"]
        min_all, max_all = [], []
        for data in datalist:
            nonzero_data = list(filter(lambda x: (x != 0), data))
            if scale == 1 and len(nonzero_data) > 0:
                min_all.append(min(nonzero_data))
            else:
                min_all.append(min(data))
            max_all.append(max(data))
        min_all = min(min_all)
        max_all = max(max_all)
        span = max_all - min_all
        if scale == 0:
            padding_factor = 0.05 if count % 2 else 0.015
            min_all -= padding_factor * span
            max_all += padding_factor * span
        elif count % 2:
            min_all *= 0.5
            max_all *= 2
        self.props.figure_settings.set_property(f"min_{direction}", min_all)
        self.props.figure_settings.set_property(f"max_{direction}", max_all)
    self.props.view_clipboard.add()


def change_scale(action, target, self, prop):
    self.props.figure_settings.set_property(
        prop, 0 if target.get_string() == "linear" else 1,
    )
    action.change_state(target)


def get_next_color(items):
    """Get the color that is to be used for the next data set"""
    color_cycle = pyplot.rcParams["axes.prop_cycle"].by_key()["color"]
    used_colors = []
    for item in items:
        used_colors.append(item.color)
        # If we've got all colors once, remove those from used_colors so we
        # can loop around
        if set(used_colors) == set(color_cycle):
            for color in color_cycle:
                used_colors.remove(color)

    for color in color_cycle:
        if color not in used_colors:
            return color
