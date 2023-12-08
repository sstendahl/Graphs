# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Graphs

# Type hints
ItemList = list[Graphs.Item]
Limits = tuple[float, float, float, float]


class ParseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


LEGEND_POSITIONS = [
    "best", "upper right", "upper left", "lower left", "lower right",
    "center left", "center right", "lower center", "upper center", "center",
]
DELIMITERS = {
    "whitespace": "\\s+", "tabs": "\\t+", "colon": ":", "semicolon": ";",
    "comma": ",", "period": ".", "custom": "custom",
}
LINESTYLES = ["none", "solid", "dotted", "dashed", "dashdot"]
MARKERSTYLES = [
    "none", ".", ",", "o", "v", "^", "<", ">", "8", "s", "p", "*", "h", "H",
    "+", "x", "D", "d", "|", "_", "P", "X",
]
LIMITS = [
    "min_bottom", "max_bottom", "min_top", "max_top",
    "min_left", "max_left", "min_right", "max_right",
]


def get_delimiter(settings):
    columns_params = settings.get_child("import-params").get_child("columns")
    delimiter_value = DELIMITERS[columns_params.get_string("delimiter")]
    delimiter_value = columns_params.get_string("custom-delimiter") \
        if delimiter_value == "custom" else delimiter_value
    return delimiter_value
