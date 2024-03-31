# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for file operations."""
import io
import json
from xml.dom import minidom

from gi.repository import GLib, Gio, Graphs

from graphs import item, ui


class FileLikeWrapper(io.BufferedIOBase):
    """FileLike Wrapper for Gio.Files."""

    def __init__(self, read_stream=None, write_stream=None):
        self._read_stream, self._write_stream = read_stream, write_stream

    @classmethod
    def new_for_io_stream(cls, io_stream: Gio.IOStream):
        """Create a wrapper for an IOStream."""
        return cls(
            read_stream=io_stream.get_input_stream(),
            write_stream=io_stream.get_output_stream(),
        )

    @property
    def closed(self) -> bool:
        """Whether or not the stream is closed."""
        return self._read_stream is None and self._write_stream is None

    def close(self) -> None:
        """Close the stream."""
        if self._read_stream is not None:
            self._read_stream.close()
            self._read_stream = None
        if self._write_stream is not None:
            self._write_stream.close()
            self._write_stream = None

    def writable(self) -> bool:
        """Whether or not the stream can be written to."""
        return self._write_stream is not None

    def write(self, b) -> int:
        """Write to the stream."""
        if self._write_stream is None:
            raise OSError()
        elif b is None or b == b"":
            return 0
        return self._write_stream.write_bytes(GLib.Bytes(b))

    def readable(self) -> bool:
        """Whether or not the stream can be read from."""
        return self._read_stream is not None

    def read(self, size=-1):
        """Read from the stream."""
        if self._read_stream is None:
            raise OSError()
        elif size == 0:
            return b""
        elif size > 0:
            return self._read_stream.read_bytes(size, None).get_data()
        buffer = io.BytesIO()
        while True:
            chunk = self._read_stream.read_bytes(4096, None)
            if chunk.get_size() == 0:
                break
            buffer.write(chunk.get_data())
        return buffer.getvalue()

    read1 = read


def create_write_stream(file: Gio.File) -> Gio.OutputStream:
    """Create a write stream for a given file."""
    if file.query_exists(None):
        file.delete(None)
    return file.create(0, None)


def open_wrapped(file: Gio.File, mode: str = "rt", encoding: str = "utf-8"):
    """Open a file in a FileLike wrapper."""
    read = "r" in mode
    append = "a" in mode
    replace = "w" in mode

    def _io_stream():
        return FileLikeWrapper.new_for_io_stream(file.open_readwrite(None))

    if "x" in mode:
        if file.query_exists():
            return OSError()
        stream = create_write_stream(file)
        stream.close()
    if read and append:
        obj = _io_stream()
    elif read and replace:
        stream = create_write_stream(file)
        stream.close()
        obj = _io_stream()
    elif read:
        obj = FileLikeWrapper(read_stream=file.read(None))
    elif replace:
        obj = FileLikeWrapper(write_stream=create_write_stream(file))
    elif append:
        obj = FileLikeWrapper(write_stream=file.append(None))

    if "b" not in mode:
        obj = io.TextIOWrapper(obj, encoding=encoding)
    return obj


def iter_data_stream(stream: Gio.DataInputStream):
    """
    Iterate over a data stream.

    Note: This can be removed in the next release of pygobject.
    """
    line = stream.read_line_utf8(None)[0]
    while line is not None:
        yield line
        line = stream.read_line_utf8(None)[0]


def save_item(file: Gio.File, item_: item.DataItem) -> None:
    """Save an Item to a txt file."""
    delimiter = "\t"
    fmt = delimiter.join(["%.12e"] * 2)
    xlabel, ylabel = item_.get_xlabel(), item_.get_ylabel()
    stream = Gio.DataOutputStream.new(create_write_stream(file))
    if xlabel != "" and ylabel != "":
        stream.stream(xlabel + delimiter + ylabel + "\n")
    for values in zip(item_.xdata, item_.ydata):
        stream.put_string(fmt % values + "\n")
    stream.close()


def save_project(
    application: Graphs.Application,
    require_dialog: bool = False,
) -> None:
    """Save the current data to disk."""
    project_file = application.get_data().project_file
    if project_file is not None and not require_dialog:
        application.get_data().save()
        application.get_data().props.unsaved = False
        application.emit("project-saved")
        return
    ui.save_project_dialog(application)


def parse_json(file: Gio.File) -> dict:
    """Parse a json file to a python dict."""
    with open_wrapped(file, "rb") as wrapper:
        return json.load(wrapper)


def write_json(file: Gio.File, json_object: dict, pretty_print=True) -> None:
    """Write a python dict to a python file."""
    with open_wrapped(file, "wt") as wrapper:
        json.dump(
            json_object,
            wrapper,
            indent=4 if pretty_print else None,
            sort_keys=True,
        )


def parse_xml(file: Gio.File) -> dict:
    """Parse a xml file to a python dict."""
    with open_wrapped(file, "rb") as wrapper:
        return minidom.parse(wrapper)
