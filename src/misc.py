# SPDX-License-Identifier: GPL-3.0-or-later
class ParseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


LINESTYLES = ["none", "solid", "dotted", "dashed", "dashdot"]
MARKERSTYLES = [
    "none", ".", ",", "o", "v", "^", "<", ">", "8", "s", "p", "*", "h", "H",
    "+", "x", "D", "d", "|", "_", "P", "X",
]
