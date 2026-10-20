# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing xrdml files."""
from gettext import gettext as _
from gettext import pgettext as C_
from xml.dom import minidom

from gi.repository import Graphs

import gio_pyio

from graphs.file_import import Parser
from graphs.misc import ParseError

import numpy


class XrdmlParser(Parser):
    """Xrdml parser."""

    __gtype_name__ = "GraphsXrdmlParser"

    def __init__(self):
        super().__init__(
            "xrdml",
            C_("import-mode", "xrdml"),
            C_("file-filter", "PANalytical XRDML"),
            ["xrdml"],
        )

    @staticmethod
    def parse(
        items: Graphs.ItemList,
        settings: Graphs.ImportSettings,
        style: Graphs.StyleParameters,
    ) -> None:
        """Import data from xrdml file."""
        with gio_pyio.open(settings.get_file(), "rb") as wrapper:
            content = minidom.parse(wrapper)
        data_points = content.getElementsByTagName("dataPoints")[0]
        counting_time = _get_values(data_points, "commonCountingTime")
        # Older XRDML files store intensities, newer versions store counts
        # and optionally the beam attenuation factors
        ydata = _get_values(data_points, "intensities")
        if ydata is None:
            ydata = _get_values(data_points, "counts")
            attenuation = _get_values(data_points, "beamAttenuationFactors")
            if attenuation is not None and attenuation.size == ydata.size:
                ydata = ydata * attenuation
        ydata = ydata / counting_time[0]

        scan_type = content.getElementsByTagName("scan")
        scan_axis = scan_type[0].attributes["scanAxis"].value
        # A Gonio scan is a coupled 2Theta-Omega scan
        if scan_axis.startswith("2Theta") or scan_axis == "Gonio":
            scan_axis = "2Theta"
        if scan_axis.startswith("Omega"):
            scan_axis = "Omega"

        for position in data_points.getElementsByTagName("positions"):
            if position.attributes["axis"].value != scan_axis:
                continue
            unit = position.attributes["unit"].value
            xdata = _get_values(position, "listPositions")
            if xdata is None:
                start_pos = _get_values(position, "startPosition")[0]
                end_pos = _get_values(position, "endPosition")[0]
                xdata = numpy.linspace(start_pos, end_pos, ydata.size)
            break
        else:
            raise ParseError(_("No positions found for the scan axis"))
        item = Graphs.ItemFactory.new_data_item(
            style,
            xdata,
            ydata,
            None,
            None,
        )
        item.set_name(settings.get_filename())
        item.set_xlabel(f"{scan_axis} ({unit})")
        item.set_ylabel(_("Intensity (cps)"))
        items.add(item)


def _get_values(element, tag: str) -> numpy.ndarray | None:
    """Get the numbers in the first child element with the given tag."""
    elements = element.getElementsByTagName(tag)
    if not elements or elements[0].firstChild is None:
        return None
    return numpy.array(elements[0].firstChild.data.split(), dtype=float)
