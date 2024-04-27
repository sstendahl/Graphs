// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;

namespace Graphs {
    /**
     * Graphs application
     */
    public class Application : Adw.Application {
        public Window window { get; set; }
        public Settings settings { get; construct set; }
        public Data data { get; construct set; }
        public StyleManager figure_style_manager { get; set; }
        public bool debug { get; construct set; default = false; }

        public signal void action_invoked (string name);
        public signal void operation_invoked (string name);
        protected signal void close_request ();

        construct {
            Intl.bindtextdomain (Config.GETTEXT_PACKAGE, Config.LOCALEDIR);
            Intl.bind_textdomain_codeset (Config.GETTEXT_PACKAGE, "UTF-8");
            Intl.textdomain (Config.GETTEXT_PACKAGE);

            this.version = Config.VERSION;
        }

        /**
         * Retrieve a child of the applications settings.
         *
         * @param path a slash-separated path
         */
        public Settings get_settings_child (string path) {
            Settings settings = this.settings;
            foreach (string child_name in path.split ("/")) {
                settings = settings.get_child (child_name);
            }
            return settings;
        }

        public void close () {
            this.close_request.emit ();
        }
    }
}
