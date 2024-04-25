# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate Graphs GResource at build time."""
import argparse
import importlib.util
import logging
import sys
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image

from gi.repository import Gio

import numpy

from matplotlib import font_manager

parser = argparse.ArgumentParser(
    description="Generate Graphs GResource at build time.",
)
parser.add_argument(
    "out",
    help="The output file",
)
parser.add_argument(
    "dir",
    help="Path to build directory",
)
parser.add_argument(
    "style_io",
    help="Path to style_io.py",
)
parser.add_argument(
    "--ui",
    required=True,
    nargs="+",
    dest="ui",
    help="List of UI Files.",
)
parser.add_argument(
    "--styles",
    required=True,
    nargs="+",
    dest="styles",
    help="List of Styles.",
)
parser.add_argument(
    "--other",
    required=True,
    nargs="+",
    dest="other",
    help="List of other Files to include at toplevel.",
)
parser.add_argument(
    "--icons",
    required=True,
    nargs="+",
    dest="icons",
    help="List of icon Files.",
)
args = parser.parse_args()

# Check fonts
font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
for font in font_list:
    try:
        font_manager.fontManager.addfont(font)
    except RuntimeError:
        logging.warning(f"Could not load {font}")
# Disable matplotlib logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# dynamically import style_io
spec = importlib.util.spec_from_file_location("style_io", args.style_io)
style_io = importlib.util.module_from_spec(spec)
sys.modules["style_io"] = style_io
spec.loader.exec_module(style_io)

# GResource tree creation
gresources = ElementTree.Element("gresources")
main_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": "/se/sjoerd/Graphs/"},
)

# Begin Other Section
for file in args.other:
    path = Path(file)
    element = ElementTree.SubElement(
        main_gresource,
        "file",
        attrib={
            "compressed": "True", "alias": path.name
        },
    )
    element.text = str(path)
# End Other Section

# Begin style section
styles = {}
styles_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": "/se/sjoerd/Graphs/styles/"},
)
for style_path in args.styles:
    name = Path(style_path).name
    style_element = ElementTree.SubElement(
        styles_gresource,
        "file",
        attrib={
            "compressed": "True",
            "alias": name,
        },
    )
    style_element.text = str(Path(style_path))
    params_file = Gio.File.new_for_path(style_path)
    params, stylename = style_io.parse(params_file)
    out_path = Path(args.dir, name.replace(".mplstyle", ".png"))
    styles[stylename] = out_path
    with open(out_path, "wb") as out_file:
        style_io.create_preview(out_file, params, "png")
    preview_element = ElementTree.SubElement(
        main_gresource,
        "file",
        attrib={
            "compressed": "True",
            "alias": out_path.name,
        },
    )
    preview_element.text = str(out_path)


def _to_array(file_path):
    with open(file_path, "rb") as file:
        return numpy.array(Image.open(file).convert("RGB"))


# Generate stitched system previews for Adwaita and Yaru
for sys_style in ("Adwaita", "Yaru"):
    light_array = _to_array(styles[sys_style])
    dark_array = _to_array(styles[sys_style + " Dark"])
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
            "alias": out_path.name,
        },
    )
    preview_element.text = str(out_path)
# End style section

# Begin ui section
ui_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": "/se/sjoerd/Graphs/ui/"},
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
            "alias": path.name,
        },
    )
    ui_file_element.text = str(path)
help_overlay_element = ElementTree.SubElement(
    main_gresource,
    "file",
    attrib={
        "preprocess": "xml-stripblanks",
        "alias": "gtk/help-overlay.ui",
    },
)
help_overlay_element.text = str(help_overlay_path)
# End ui section

# Begin icon section
icon_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": "/se/sjoerd/Graphs/icons/scalable/actions/"},
)
for icon_file in args.icons:
    path = Path(icon_file)
    icon_file_element = ElementTree.SubElement(
        icon_gresource,
        "file",
        attrib={
            "preprocess": "xml-stripblanks",
            "alias": path.name,
        },
    )
    icon_file_element.text = str(path)
# End icon section

# Write
tree = ElementTree.ElementTree(gresources)
tree.write(args.out)
