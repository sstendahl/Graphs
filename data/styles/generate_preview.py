#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Generate a style preview.

Used at build time by meson, but is build-system-independent.
"""
import argparse
import importlib.util
import io
import logging
import sys
from pathlib import Path

from PIL import Image

from gi.repository import Gio

from matplotlib import font_manager

import numpy

parser = argparse.ArgumentParser(description="Generate Graphs style preview.")
parser.add_argument("style_io", help="Path to `style_io.py`.", type=Path)
subparsers = parser.add_subparsers(dest="command")
preview_parser = subparsers.add_parser(
    "preview",
    help="Generate a style preview.",
)
preview_parser.add_argument("input", type=Path)
preview_parser.add_argument("preview", type=argparse.FileType("wb"))
system_parser = subparsers.add_parser(
    "system",
    help="Generate a system preview by stitching to previews",
)
system_parser.add_argument("light", type=Path)
system_parser.add_argument("dark", type=Path)
system_parser.add_argument("preview", type=argparse.FileType("wb"))
args = parser.parse_args()

# Check fonts
font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
for font in font_list:
    try:
        font_manager.fontManager.addfont(font)
    except RuntimeError:
        if args.command is None:
            logging.warning("Could not load %s", font)
# Disable matplotlib logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# dynamically import style_io
spec = importlib.util.spec_from_file_location("style_io", args.style_io)
style_io = importlib.util.module_from_spec(spec)
sys.modules["style_io"] = style_io
spec.loader.exec_module(style_io)


def _create_preview(file_path: Path, out) -> None:
    g_file = Gio.File.new_for_path(str(file_path))
    params = style_io.parse(g_file)
    style_io.create_preview(out, params, "png", 31)


def _to_array(file_path: Path) -> numpy.ndarray:
    buffer = io.BytesIO()
    _create_preview(file_path, buffer)
    return numpy.array(Image.open(buffer).convert("RGB"))


if args.command == "preview":
    _create_preview(args.input, args.preview)

if args.command == "system":
    light_array = _to_array(args.light)
    dark_array = _to_array(args.dark)
    height, width = light_array.shape[0:2]
    stitched_array = numpy.concatenate(
        (light_array[:, :width // 2], dark_array[:, width // 2:]),
        axis=1,
    )
    stitched_image = Image.fromarray(stitched_array)
    stitched_image.save(args.preview, "PNG")
