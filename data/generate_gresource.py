#!/usr/bin/python
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Generate Graphs GResource.

Used at build time by meson, but is build-system-independent.
"""
import argparse
import importlib.util
import logging
import shutil
import sys
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image

from gi.repository import Gio

from matplotlib import font_manager

import numpy

parser = argparse.ArgumentParser(description="Generate Graphs gresource.")
parser.add_argument(
    "out",
    help="the output file",
)
parser.add_argument(
    "dir",
    help="Path to build directory. Files provided will be copied there.",
)
parser.add_argument(
    "style_io",
    help="Path to `style_io.py`. Used to generate style previews.",
)
parser.add_argument(
    "--ui",
    required=True,
    nargs="+",
    dest="ui",
    help="List of UI files.",
)
parser.add_argument(
    "--styles",
    required=True,
    nargs="+",
    dest="styles",
    help="List of style files.",
)
parser.add_argument(
    "--other",
    required=True,
    nargs="+",
    dest="other",
    help="List of other files to include.",
)
parser.add_argument(
    "--icons",
    required=True,
    nargs="+",
    dest="icons",
    help="List of icon files.",
)
args = parser.parse_args()

# Check fonts
font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
for font in font_list:
    try:
        font_manager.fontManager.addfont(font)
    except RuntimeError:
        logging.warning("Could not load %s", font)
# Disable matplotlib logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# dynamically import style_io
spec = importlib.util.spec_from_file_location("style_io", args.style_io)
style_io = importlib.util.module_from_spec(spec)
sys.modules["style_io"] = style_io
spec.loader.exec_module(style_io)

# GResource tree creation
gresources = ElementTree.Element("gresources")
main_prefix = "/se/sjoerd/Graphs/"
main_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": main_prefix},
)

# Begin Other Section
for file in args.other:
    name = Path(shutil.copy(file, args.dir)).name
    element = ElementTree.SubElement(
        main_gresource,
        "file",
        attrib={
            "compressed": "True",
        },
    )
    element.text = name
# End Other Section

# Begin style section
styles = []
style_paths = {}
style_prefix = main_prefix + "styles/"
styles_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": style_prefix},
)
style_list = Path(args.dir, "styles.txt")
for style_path in args.styles:
    style_file = shutil.copy(style_path, args.dir)
    name = Path(style_file).name
    style_element = ElementTree.SubElement(
        styles_gresource,
        "file",
        attrib={
            "compressed": "True",
        },
    )
    style_element.text = name
    params, graphs_paramns = style_io.parse(Gio.File.new_for_path(style_file))
    stylename = graphs_paramns["name"]
    out_path = Path(args.dir, name.replace(".mplstyle", ".png"))
    style_paths[stylename] = out_path
    with open(out_path, "wb") as out_file:
        style_io.create_preview(out_file, params, "png")
    preview_element = ElementTree.SubElement(
        main_gresource,
        "file",
        attrib={
            "compressed": "True",
        },
    )
    preview_element.text = out_path.name
    styles.append(
        (stylename, style_prefix + name, main_prefix + out_path.name),
    )
styles.sort(key=lambda x: x[0].casefold())
with open(style_list, "wt") as style_list_file:
    style_list_file.writelines(";".join(x) + "\n" for x in styles)
style_list_element = ElementTree.SubElement(
    main_gresource,
    "file",
    attrib={
        "compressed": "True",
    },
)
style_list_element.text = style_list.name


def _to_array(file_path):
    with open(file_path, "rb") as file:
        return numpy.array(Image.open(file).convert("RGB"))


# Generate stitched system previews for Adwaita and Yaru
for sys_style in ("Adwaita", "Yaru"):
    light_array = _to_array(style_paths[sys_style])
    dark_array = _to_array(style_paths[sys_style + " Dark"])
    height, width = light_array.shape[0:2]
    stitched_array = numpy.concatenate(
        (light_array[:, :width // 2], dark_array[:, width // 2:]),
        axis=1,
    )
    stitched_image = Image.fromarray(stitched_array)
    out_path = Path(args.dir + "/system-style-" + sys_style.lower() + ".png")
    with open(out_path, "wb") as file:
        stitched_image.save(file, "PNG")
    preview_element = ElementTree.SubElement(
        main_gresource,
        "file",
        attrib={
            "compressed": "True",
        },
    )
    preview_element.text = out_path.name
# End style section

# Begin ui section
ui_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": main_prefix},
)
help_overlay_path = None
for ui_file in args.ui:
    path = Path(ui_file)
    if path.name == "shortcuts.ui":
        help_overlay_path = path
        continue
    ui_file_element = ElementTree.SubElement(
        ui_gresource,
        "file",
        attrib={
            "preprocess": "xml-stripblanks",
        },
    )
    ui_file_element.text = "ui/" + path.name
help_overlay_element = ElementTree.SubElement(
    ui_gresource,
    "file",
    attrib={
        "preprocess": "xml-stripblanks",
        "alias": "gtk/help-overlay.ui",
    },
)
help_overlay_element.text = "ui/" + help_overlay_path.name
# End ui section

# Begin icon section
icon_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": main_prefix + "icons/scalable/actions/"},
)
for icon_file in args.icons:
    path = Path(Path(shutil.copy(icon_file, args.dir)))
    icon_file_element = ElementTree.SubElement(
        icon_gresource,
        "file",
        attrib={
            "preprocess": "xml-stripblanks",
        },
    )
    icon_file_element.text = path.name
# End icon section

# Write
tree = ElementTree.ElementTree(gresources)
tree.write(args.out)
