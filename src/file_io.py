# SPDX-License-Identifier: GPL-3.0-or-later
import io
import json
from xml.dom import minidom

from gi.repository import GLib, Gio

from graphs import ui


class FileLikeWrapper(io.BufferedIOBase):
    def __init__(self, read_stream=None, write_stream=None):
        self._read_stream, self._write_stream = read_stream, write_stream

    @classmethod
    def new_for_io_stream(cls, io_stream: Gio.IOStream):
        return cls(
            read_stream=io_stream.get_input_stream(),
            write_stream=io_stream.get_output_stream(),
        )

    @property
    def closed(self) -> bool:
        return self._read_stream is None and self._write_stream is None

    def close(self) -> None:
        if self._read_stream is not None:
            self._read_stream.close()
            self._read_stream = None
        if self._write_stream is not None:
            self._write_stream.close()
            self._write_stream = None

    def writable(self) -> bool:
        return self._write_stream is not None

    def write(self, b) -> int:
        if self._write_stream is None:
            raise OSError()
        elif b is None or b == b"":
            return 0
        return self._write_stream.write_bytes(GLib.Bytes(b))

    def readable(self) -> bool:
        return self._read_stream is not None

    def read(self, size=-1):
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


def open_wrapped(file: Gio.File, mode: str = "rt", encoding: str = "utf-8"):
    read = "r" in mode
    append = "a" in mode
    replace = "w" in mode

    def _create_stream():
        if file.query_exists(None):
            file.delete(None)
        return file.create(0, None)

    def _io_stream():
        return FileLikeWrapper.new_for_io_stream(file.open_readwrite(None))

    if "x" in mode:
        if file.query_exists():
            return OSError()
        stream = _create_stream()
        stream.close()
    if read and append:
        obj = _io_stream()
    elif read and replace:
        stream = _create_stream()
        stream.close()
        obj = _io_stream()
    elif read:
        obj = FileLikeWrapper(read_stream=file.read(None))
    elif replace:
        obj = FileLikeWrapper(write_stream=_create_stream())
    elif append:
        obj = FileLikeWrapper(write_stream=file.append(None))

    if "b" not in mode:
        obj = io.TextIOWrapper(obj, encoding=encoding)
    return obj


def save_item(file, item_):
    delimiter = "\t"
    fmt = delimiter.join(["%.12e"] * 2)
    xlabel, ylabel = item_.get_xlabel(), item_.get_ylabel()
    with open_wrapped(file, "wt") as wrapper:
        if xlabel != "" and ylabel != "":
            wrapper.write(xlabel + delimiter + ylabel + "\n")
        for values in zip(item_.xdata, item_.ydata):
            wrapper.write(fmt % values + "\n")


def save_project(self, require_dialog=False):
    project_file = self.get_data().project_file
    if project_file is not None and not require_dialog:
        self.get_data().save()
        self.get_data().props.unsaved = False
        self.emit("project-saved")
        return
    ui.save_project_dialog(self)


def parse_json(file):
    with open_wrapped(file, "rb") as wrapper:
        return json.load(wrapper)


def write_json(file, json_object, pretty_print=True):
    with open_wrapped(file, "wt") as wrapper:
        json.dump(
            json_object, wrapper,
            indent=4 if pretty_print else None, sort_keys=True,
        )


def parse_xml(file):
    with open_wrapped(file, "rb") as wrapper:
        return minidom.parse(wrapper)
