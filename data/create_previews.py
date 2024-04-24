# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate Style previews at build time."""
import importlib.util
import sys

from PIL import Image

from gi.repository import Gio

import numpy

# dynamically import style_io
spec = importlib.util.spec_from_file_location("style_io", sys.argv[1])
style_io = importlib.util.module_from_spec(spec)
sys.modules["style_io"] = style_io
spec.loader.exec_module(style_io)

num_styles = int(len(sys.argv[2:]) / 2)
in_files = sys.argv[2:2 + num_styles]
out_files = sys.argv[2 + num_styles:]

styles = {}

for in_file_path, out_file_path in zip(in_files, out_files):
    params_file = Gio.File.new_for_path(in_file_path)
    params, name = style_io.parse(params_file)
    styles[name] = out_file_path

    with open(out_file_path, "wb") as out_file:
        style_io.create_preview(out_file, params, "png")


def _to_array(file_path):
    with open(file_path, "rb") as file:
        return numpy.array(Image.open(file).convert("RGB"))


# Generate stitched system previews for Adwaita and Yaru
for sys_style in ("Adwaita", "Yaru"):
    light_array = _to_array(styles[sys_style])
    dark_array = _to_array(styles[sys_style + " Dark"])
    height, width = light_array.shape[0:2]
    stitched_array = numpy.concatenate(
        (light_array[:, :width // 2], dark_array[:, width // 2:]), axis=1,
    )
    stitched_image = Image.fromarray(stitched_array)
    out_path = "data/system-style-" + sys_style.lower() + ".png"
    with open(out_path, "wb") as file:
        stitched_image.save(file, "PNG")
