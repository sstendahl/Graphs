# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for parsing xrdml files."""
from gettext import gettext as _
from gettext import pgettext as C_

from graphs import file_io, item, misc
from graphs.file_import.parsers import Parser

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
    def parse(settings, style) -> misc.ItemList:
        """Import data from xrdml file."""
        content = file_io.parse_xml(settings.get_file())
        intensities = content.getElementsByTagName("intensities")
        counting_time = content.getElementsByTagName("commonCountingTime")
        counting_time = float(counting_time[0].firstChild.data)
        ydata = intensities[0].firstChild.data.split()
        ydata = [int(value) / counting_time for value in ydata]

        scan_type = content.getElementsByTagName("scan")
        scan_axis = scan_type[0].attributes["scanAxis"].value
        if scan_axis.startswith("2Theta"):
            scan_axis = "2Theta"
        if scan_axis.startswith("Omega"):
            scan_axis = "Omega"

        data_points = content.getElementsByTagName("positions")
        for position in data_points:
            axis = position.attributes["axis"]
            if axis.value == scan_axis:
                unit = position.attributes["unit"].value
                start_pos = position.getElementsByTagName("startPosition")
                end_pos = position.getElementsByTagName("endPosition")
                start_pos = float(start_pos[0].firstChild.data)
                end_pos = float(end_pos[0].firstChild.data)
                xdata = numpy.linspace(start_pos, end_pos, len(ydata))
                xdata = numpy.ndarray.tolist(xdata)
        return [
            item.DataItem.new(
                style,
                xdata,
                ydata,
                name=settings.get_filename(),
                xlabel=f"{scan_axis} ({unit})",
                ylabel=_("Intensity (cps)"),
            ),
        ]
