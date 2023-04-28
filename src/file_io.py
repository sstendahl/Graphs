# SPDX-License-Identifier: GPL-3.0-or-later
import os
import pickle
import re
from xml.dom import minidom

from graphs import utilities

import numpy


def save_project(path, plot_settings, datadict, datadict_clipboard,
                 clipboard_pos, version):
    project_data = {
        "plot_settings": plot_settings,
        "data": datadict,
        "datadict_clipboard": datadict_clipboard,
        "clipboard_pos": clipboard_pos,
        "version": version,
    }
    with open(path, "wb") as file:
        pickle.dump(project_data, file)


def load_project(path):
    with open(path, "rb") as file:
        project = pickle.load(file)
        return project["plot_settings"], project["data"], \
            project["datadict_clipboard"], project["clipboard_pos"], \
            project["version"]


def save_file(self, path):
    if len(self.datadict) == 1:
        for item in self.datadict.values():
            xdata = item.xdata
            ydata = item.ydata
        array = numpy.stack([xdata, ydata], axis=1)
        numpy.savetxt(str(path), array, delimiter="\t")
    elif len(self.datadict) > 1:
        for item in self.datadict.values():
            xdata = item.xdata
            ydata = item.ydata
            filename = item.name.replace("/", "")
            array = numpy.stack([xdata, ydata], axis=1)
            file_path = f"{path}/{filename}.txt"
            if os.path.exists(file_path):
                file_path = f"{path}/{filename} (copy).txt"
            numpy.savetxt(str(file_path), array, delimiter="\t")


def get_xrdml(self, import_settings):
    path = import_settings.path
    file = minidom.parse(path)
    intensities = file.getElementsByTagName("intensities")
    counting_time = file.getElementsByTagName("commonCountingTime")
    counting_time = float(counting_time[0].firstChild.data)
    ydata = intensities[0].firstChild.data.split()
    ydata = [int(value) / counting_time for value in ydata]

    scan_type = file.getElementsByTagName("scan")
    scan_axis = scan_type[0].attributes["scanAxis"].value
    if scan_axis.startswith("2Theta"):
        scan_axis = "2Theta"
    if scan_axis.startswith("Omega"):
        scan_axis = "Omega"

    data_points = file.getElementsByTagName("positions")
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

    self.plot_settings.xlabel = f"{scan_axis} ({unit})"
    self.plot_settings.ylabel = "Intensity (cps)"
    return xdata, ydata


def get_xry(self, import_settings):
    """
    Import data from .xry files used by Leybold X-ray apparatus.

    Slightly modified version of
    https://github.com/rdbeerman/Readxry/blob/master/manual.py
    """
    with open(import_settings.path, "r", encoding="ISO-8859-1") as file:
        rawdata = [line.strip() for line in file.readlines()]
        b_min = float(rawdata[4].split()[0])
        b_max = float(rawdata[4].split()[1])

        ydata = numpy.array(rawdata[18:-11]).astype(float)
        xdata = numpy.arange(b_min, b_max, (b_max - b_min) / len(ydata))

        self.plot_settings.xlabel = "β (°)"
        self.plot_settings.ylabel = "Intensity (s⁻¹)"
        return xdata, ydata


def get_column_file(self, import_settings):
    data_array = [[], []]
    path = import_settings.path
    with open(path, "r", encoding="utf-8") as file:
        for i, line in enumerate(file):
            if i > import_settings.skip_rows:
                line = line.strip()
                data_line = re.split(str(import_settings.delimiter), line)
                if import_settings.separator == ",":
                    for index, value in enumerate(data_line):
                        data_line[index] = utilities.swap(value)
                if utilities.check_if_floats(data_line):
                    if len(data_line) == 1:
                        data_array[0].append(i)
                        data_array[1].append(float(data_line[0]))
                    else:
                        data_array[0].append(float(data_line[
                            import_settings.column_x]))
                        data_array[1].append(float(data_line[
                            import_settings.column_y]))
                # If not all values in the line are floats, start looking for
                # headers instead
                else:
                    if import_settings.guess_headers:
                        # By default it will check for headers using at least
                        # two whitespaces as delimiter (often tabs), but if
                        # that doesn"t work it will try the same delimiter as
                        # used for the data import itself The reasoning is that
                        # some people use tabs for the headers, but e.g. commas
                        # for the data
                        try:
                            headers = re.split("\\s{2,}", line)
                            self.plot_settings.xlabel = headers[
                                import_settings.column_x]
                            self.plot_settings.ylabel = headers[
                                import_settings.column_y]
                        except IndexError:
                            try:
                                headers = re.split(
                                    import_settings.delimiter, line)
                                self.plot_settings.xlabel = headers[
                                    import_settings.column_x]
                                self.plot_settings.ylabel = headers[
                                    import_settings.column_y]
                            # If neither heuristic works, we just skip headers
                            except IndexError:
                                pass
    return data_array[0], data_array[1]


def get_data(self, import_settings):
    if import_settings.path.endswith(".xrdml"):
        return get_xrdml(self, import_settings)
    if import_settings.path.endswith(".xry"):
        return get_xry(self, import_settings)
    return get_column_file(self, import_settings)


def get_style(path):
    style = {}
    with open(path, "r", encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            line = line.replace("\n", "")
            if line != "" and not line.startswith("#"):
                try:
                    key, value = line.split(": ")
                    style[key] = value
                except ValueError:
                    pass
    return style


def write_style(path, style):
    with open(path, "w", encoding="utf-8") as file:
        file.write(f"# {style['name']}\n")
        for key, value in style.items():
            if key != "name":
                file.write(f"{key}: {value}\n")
