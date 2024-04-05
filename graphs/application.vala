// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;

namespace Graphs {
    public class Application : Adw.Application {
        public Window window { get; set; }
        public Settings settings { get; construct set; }
        public DataInterface data { get; construct set; }
        public StyleManagerInterface figure_style_manager { get; set; }
        public int mode { get; set; default = 0; }
        public bool debug { get; construct set; default = false; }

        protected signal void scales ();

        construct {
            Intl.bindtextdomain (Config.GETTEXT_PACKAGE, Config.LOCALEDIR);
            Intl.bind_textdomain_codeset (Config.GETTEXT_PACKAGE, "UTF-8");
            Intl.textdomain (Config.GETTEXT_PACKAGE);

            this.version = Config.VERSION;
        }

        protected void setup_actions () {
            SimpleAction toggle_sidebar_action = new SimpleAction.stateful (
                "toggle_sidebar",
                null,
                new Variant.boolean (true)
            );
            toggle_sidebar_action.activate.connect (() => {
                OverlaySplitView split_view = this.window.split_view;
                split_view.collapsed = !split_view.collapsed;
            });
            this.add_action (toggle_sidebar_action);

            string[] modes = {"pan", "zoom", "select"};
            foreach (string mode in modes) {
                SimpleAction action = new SimpleAction (@"mode_$mode", null);
                action.activate.connect (() => {
                    switch (mode) {
                        case "pan": {
                            this.mode = 0;
                            break;
                        }
                        case "zoom": {
                            this.mode = 1;
                            break;
                        }
                        case "select": {
                            this.mode = 2;
                            break;
                        }
                    }
                });
                this.add_action (action);
            }

            string[] settings_actions = {"center", "smoothen"};
            Settings actions_settings = this.settings.get_child ("actions");
            foreach (string settings_action in settings_actions) {
                this.add_action (actions_settings.create_action (settings_action));
            }
        }

        public Settings get_settings_child (string path) {
            Settings settings = this.settings;
            foreach (string child_name in path.split ("/")) {
                settings = settings.get_child (child_name);
            }
            return settings;
        }
    }
}

