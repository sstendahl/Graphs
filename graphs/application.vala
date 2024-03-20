// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;

namespace Graphs {
    public class Application : Adw.Application {
        public Window window { get; set; }
        public Settings settings { get; construct set; }
        public DataInterface data { get; construct set; }
        public StyleManagerInterface figure_style_manager { get; set; }
        public int mode { get; set; default = 0; }
        public string name { get; construct set; default = ""; }
        public string website { get; construct set; default = ""; }
        public string issues { get; construct set; default = ""; }
        public string author { get; construct set; default = ""; }
        public string pkgdatadir { get; construct set; default = ""; }
        public bool ctrl { get; construct set; default = false; }
        public bool shift { get; construct set; default = false; }

        public Settings get_settings_child (string path) {
            Settings settings = this.settings;
            foreach (string child_name in path.split ("/")) {
                settings = settings.get_child (child_name);
            }
            return settings;
        }
    }
}

