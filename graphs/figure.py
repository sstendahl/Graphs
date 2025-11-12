# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Tuple
from matplotlib import figure, RcParams, pyplot

from gi.repository import GObject, Gio

class Figure(GObject.Object, figure.Figure):

    __gtype_name__ = "GraphsFigure"

    def __init__(
        self,
        style_params: Tuple[RcParams, dict],
        items: Gio.ListModel,
    ):
        GObject.Object.__init__(self)
        self._style_params = style_params
        pyplot.rcParams.update(self._style_params[0])  # apply style_params
        figure.Figure.__init__(self, tight_layout=True)

    def set_properties(*args):
        figure.Figure.set_properties(*args)

    def set_property(*args):
        figure.Figure.set_property(*args)
