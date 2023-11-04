# SPDX-License-Identifier: GPL-3.0-or-later
import io
import json
from xml.dom import minidom

from gi.repository import GLib, Gio


class FileLikeWrapper(io.BufferedIOBase):
    def __init__(self, read_stream=None, write_stream=None):
        self._read_stream, self._write_stream = read_stream, write_stream

    @classmethod
    def new_for_file_replace(cls, file: Gio.File):
        if file.query_exists(None):
            file.delete(None)
        return cls(write_stream=file.create(0, None))

    @classmethod
    def new_for_file(cls, file: Gio.File):
        return cls.new_for_io_stream(file.open_readwrite(None))

    @classmethod
    def new_for_file_readonly(cls, file: Gio.File):
        return cls(read_stream=file.read(None))

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
            return self._read_stream.read_bytes(size, None)
        else:
            buffer = io.BytesIO()
            while True:
                chunk = self._read_stream.read_bytes(4096, None)
                if chunk.get_size() == 0:
                    break
                buffer.write(chunk.get_data())
            return buffer.getvalue()


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
    wrapper = FileLikeWrapper.new_for_file_readonly(file)
    return json.load(wrapper)
    wrapper.close()


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
