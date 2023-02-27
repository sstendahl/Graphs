# SPDX-License-Identifier: GPL-3.0-or-later
import os
import pickle
import re

from graphs import utilities

import numpy


def save_project(path, plot_settings, datadict, version):
    project_data = {
        "plot_settings": plot_settings,
        "data": datadict,
        "version": version
    }
    with open(path, "wb") as file:
        pickle.dump(project_data, file)


def load_project(path):
    with open(path, "rb") as file:
        project = pickle.load(file)
        return project["plot_settings"], project["data"], project["version"]


def save_file(self, path):
    if len(self.datadict) == 1:
        for _key, item in self.datadict.items():
            xdata = item.xdata
            ydata = item.ydata
        filename = path
        array = numpy.stack([xdata, ydata], axis=1)
        numpy.savetxt(str(filename), array, delimiter="\t")
    elif len(self.datadict) > 1:
        for _key, item in self.datadict.items():
            xdata = item.xdata
            ydata = item.ydata
            filename = item.filename
            array = numpy.stack([xdata, ydata], axis=1)
            if os.path.exists(f"{path}/{filename}.txt"):
                numpy.savetxt(str(path + "/" + filename) + " (copy).txt",
                              array, delimiter="\t")
            else:
                numpy.savetxt(str(path + "/" + filename) + ".txt", array,
                              delimiter="\t")


def get_data(self, import_settings):
    data_array = [[], []]
    i = 0
    path = import_settings.path
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            i += 1
            if i > import_settings.skip_rows:
                line = line.strip()
                data_line = re.split(str(import_settings.delimiter), line)
                if import_settings.separator == ",":
                    for index, value in enumerate(data_line):
                        data_line[index] = utilities.swap(value)
                try:
                    data_array[0].append(float(data_line[
                        import_settings.column_x]))
                    data_array[1].append(float(data_line[
                        import_settings.column_y]))

                # If it finds non-numbers, it will raise a ValueError,
                # this is the cue to start looking for headers
                except ValueError:
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
                                    import_settings["delimiter"], line)
                                self.plot_settings.xlabel = headers[
                                    import_settings.column_x]
                                self.plot_settings.ylabel = headers[
                                    import_settings.column_y]
                            # If neither heuristic works, we just skip headers
                            except IndexError:
                                pass
    return data_array[0], data_array[1]
