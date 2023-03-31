# SPDX-License-Identifier: GPL-3.0-or-later
import os
import shutil
from pathlib import Path

from graphs import utilities


def get_system_styles(self):
    path = os.path.join(self.modulepath, "styles")
    styles = {}
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            styles[Path(file).stem] = os.path.join(path, file)
    return styles


def get_user_styles(self):
    path = os.path.join(utilities.get_config_path(), "styles")
    if not os.path.exists(path):
        reset_user_styles(self)
    styles = {}
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            styles[Path(file).stem] = os.path.join(path, file)
    if not styles:
        reset_user_styles(self)
        styles = get_user_styles(self)
    return styles


def reset_user_styles(self):
    user_path = os.path.join(utilities.get_config_path(), "styles")
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    os.chdir(user_path)
    for file in os.listdir(user_path):
        if os.path.isfile(os.path.join(user_path, file)):
            os.remove(file)
    for style, path in get_system_styles(self).items():
        shutil.copy(path, os.path.join(user_path, f"{style}.mplstyle"))
