// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gdk;
using Gtk;
using Gee;

namespace Graphs {
    private const string[] X_DIRECTIONS = {"top", "bottom"};
    private const string[] Y_DIRECTIONS = {"left", "right"};

    /**
     * Graphs application
     */
    public class Application : Adw.Application {
        public Window? window { get; set; }
        public GLib.Settings settings { get; construct set; }
        public Data data { get; construct set; }
        public StyleManager figure_style_manager { get; set; }
        public bool debug { get; construct set; default = false; }
        public PythonHelper python_helper { get; construct set; }
        public CssProvider css_provider { get; construct set; }

        public signal void operation_invoked (string name);

        private uint style_editors = 0;

        construct {
            Intl.bindtextdomain (Config.GETTEXT_PACKAGE, Config.LOCALEDIR);
            Intl.bind_textdomain_codeset (Config.GETTEXT_PACKAGE, "UTF-8");
            Intl.textdomain (Config.GETTEXT_PACKAGE);

            this.version = Config.VERSION;
        }

        /**
         * Setup the application.
         */
        public override void startup () {
            base.startup ();

            this.css_provider = new CssProvider ();
            StyleContext.add_provider_for_display (
                Display.get_default (),
                css_provider,
                STYLE_PROVIDER_PRIORITY_APPLICATION
            );

            var help_action = new SimpleAction ("help", null);
            help_action.activate.connect (() => {
                try {
                    AppInfo.launch_default_for_uri (
                        "help:graphs",
                        window.get_display ().get_app_launch_context ()
                    );
                } catch { assert_not_reached (); }
            });
            add_action (help_action);
            set_accels_for_action ("app.help", {"F1"});
        }

        /**
         * Activate the application.
         */
        public override void activate () {
            base.activate ();
            if (window == null) {
                this.window = new Window (this);
                python_helper.run_method (this, "_reload_canvas");
                window.present ();
            }
        }

        /**
         * Handle File Opening.
         */
        public override void open (File[] files, string hint) {
            base.open (files, hint);
            activate ();
            if (files.length == 1) {
                File file = files[0];
                string uri = file.get_uri ();

                if (uri.has_suffix (".graphs")) {
                    if (data.unsaved) {
                        var dialog = Tools.build_dialog ("save_changes") as Adw.AlertDialog;
                        dialog.response.connect ((d, response) => {
                            if (response == "discard_close") {
                                data.file = file;
                                data.load ();
                            } else if (response == "save_close") {
                                Project.save.begin (this, false, (o, result) => {
                                    Project.save.end (result);
                                    data.file = file;
                                    data.load ();
                                });
                            }
                        });
                        dialog.present (window);
                    } else {
                        data.file = file;
                        data.load ();
                    }
                } else if (uri.has_suffix (".mplstyle")) {
                    python_helper.open_style_editor (file);
                }
            } else {
                python_helper.import_from_files (files);
            }
        }

        /**
         * Retrieve a child of the applications settings.
         *
         * @param path a slash-separated path
         */
        public GLib.Settings get_settings_child (string path) {
            GLib.Settings settings_child = settings;
            foreach (string child_name in path.split ("/")) {
                settings_child = settings_child.get_child (child_name);
            }
            return settings_child;
        }

        public void register_style_editor () {
            style_editors++;
        }

        public void on_main_window_closed () {
            this.window = null;
            try_quit ();
        }

        public void on_style_editor_closed () {
            style_editors--;
            try_quit ();
        }

        private void try_quit () {
            if (window == null && style_editors == 0) {
                quit ();
            }
        }
    }
}
