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

EQUATIONS = {
    "linear": "a*x+b", "quadratic": "a*x²+b*x+c", "exponential": "a*exp(b*x)",
    "power": "a*x^b", "log": "a*log(x)+b",
    "sigmoid": "L / (1 + exp(-k * (x - b)))",
    "gaussian": "a*exp(-(x-mu)²/(2*s²))",
    "custom": "custom",
}
