#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Generate Graphs GResource.

Used at build time by meson, but is build-system-independent.
"""
import argparse
from pathlib import Path
from xml.etree import ElementTree

parser = argparse.ArgumentParser(description="Generate Graphs gresource.")
parser.add_argument(
    "out",
    help="the output file",
)
parser.add_argument(
    "build_dir",
    help="Path to build directory. Generated Files will be put there.",
)
parser.add_argument(
    "source_dir",
    help="Path to source directory.",
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
    "--previews",
    required=True,
    nargs="+",
    dest="previews",
    help="List of style previews.",
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

# GResource tree creation
gresources = ElementTree.Element("gresources")
main_prefix = "/se/sjoerd/Graphs/"
main_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": main_prefix},
)
build_dir = Path(args.build_dir)
source_dir = Path(args.source_dir)

# Begin Other Section
for file in args.other:
    path = Path(file).resolve()
    element = ElementTree.SubElement(
        main_gresource,
        "file",
        attrib={
            "compressed": "True",
        },
    )
    element.text = str(path.relative_to(source_dir))
# End Other Section

# Begin style section
styles_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": main_prefix},
)
for style_path in args.styles:
    style_file = Path(style_path).resolve()
    style_element = ElementTree.SubElement(
        styles_gresource,
        "file",
        attrib={
            "compressed": "True",
        },
    )
    style_element.text = str(style_file.relative_to(source_dir))

# End style section

# Begin preview section

for preview in args.previews:
    preview_file = Path(preview).resolve()
    preview_element = ElementTree.SubElement(
        main_gresource,
        "file",
        attrib={
            "compressed": "True",
            "alias": preview_file.name,
        },
    )
    preview_element.text = str(preview_file.relative_to(build_dir))

# End preview section

# Begin ui section
ui_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": main_prefix},
)
for ui_file in args.ui:
    path = str(Path(ui_file).resolve().relative_to(build_dir))
    ui_file_element = ElementTree.SubElement(
        ui_gresource,
        "file",
        attrib={
            "preprocess": "xml-stripblanks",
            "alias": path.replace("_", "/"),
        },
    )
    ui_file_element.text = path
# End ui section

# Begin icon section
icon_gresource = ElementTree.SubElement(
    gresources,
    "gresource",
    attrib={"prefix": main_prefix + "icons/scalable/actions/"},
)
icon_dir = Path(source_dir, "icons")
for icon_file in args.icons:
    path = Path(icon_file).resolve()
    icon_file_element = ElementTree.SubElement(
        icon_gresource,
        "file",
        attrib={
            "preprocess": "xml-stripblanks",
            "alias": str(path.relative_to(icon_dir)),
        },
    )
    icon_file_element.text = str(path.relative_to(source_dir))
# End icon section

# Write
tree = ElementTree.ElementTree(gresources)
tree.write(args.out)
