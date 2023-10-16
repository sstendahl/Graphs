# SPDX-License-Identifier: GPL-3.0-or-later
import json
from xml.dom import minidom

from gi.repository import GLib


def save_item(file, item_):
    delimiter = "\t"
    fmt = delimiter.join(["%.12e"] * 2)
    stream = get_write_stream(file)
    xlabel, ylabel = item_.get_xlabel(), item_.get_ylabel()
    if xlabel != "" and ylabel != "":
        write_string(stream, xlabel + delimiter + ylabel + "\n")
    for values in zip(item_.xdata, item_.ydata):
        write_string(stream, fmt % values + "\n")
    stream.close()


def parse_json(file):
    return json.loads(file.load_bytes(None)[0].get_data())


def write_json(file, json_object, pretty_print=True):
    stream = get_write_stream(file)
    write_string(stream, json.dumps(
        json_object, indent=4 if pretty_print else None, sort_keys=True,
    ))
    stream.close()


def parse_xml(file):
    return minidom.parseString(read_file(file))


def get_write_stream(file):
    if file.query_exists(None):
        file.delete(None)
    return file.create(0, None)


def write_string(stream, line, encoding="utf-8"):
    stream.write_bytes(GLib.Bytes(line.encode(encoding)), None)


def read_file(file, encoding="utf-8"):
    content = file.load_bytes(None)[0].get_data()
    return content if encoding is None else content.decode(encoding)
