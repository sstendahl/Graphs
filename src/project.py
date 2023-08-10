# SPDX-License-Identifier: GPL-3.0-or-later


def create_project(self) -> dict:
    project = {
        "version": self.version,
        "data": [item.to_dict() for item in self.datadict.values()],
    }

    print(project)


def load_project(self, project: dict):
    pass
