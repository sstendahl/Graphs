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
        public GLib.Settings settings { get; private set; }
        public StyleManager figure_style_manager { get; protected set; }
        public bool debug { get; construct set; default = false; }
        public PythonHelper python_helper { get; protected set; }

        public signal void operation_invoked (string name);
        protected signal void setup_request ();

        private Gee.List<Window> main_windows;
        private Gee.List<StyleEditor> style_editors;

        construct {
            Intl.bindtextdomain (Config.GETTEXT_PACKAGE, Config.LOCALEDIR);
            Intl.bind_textdomain_codeset (Config.GETTEXT_PACKAGE, "UTF-8");
            Intl.textdomain (Config.GETTEXT_PACKAGE);

            this.main_windows = new Gee.LinkedList<Window> ();
            this.style_editors = new Gee.LinkedList<StyleEditor> ();

            this.version = Config.VERSION;
            this.settings = new GLib.Settings (application_id);
        }

        /**
         * Setup the application.
         */
        public override void startup () {
            base.startup ();

            Gtk.Window.set_default_icon_name (application_id);

            var quit_action = new SimpleAction ("quit", null);
            quit_action.activate.connect (() => {
                // We need to cast to array here as the list size might change
                // during iteration
                foreach (Window window in main_windows.to_array ()) {
                    window.close ();
                }
                foreach (StyleEditor style_editor in style_editors.to_array ()) {
                    style_editor.close ();
                }
            });
            add_action (quit_action);
            set_accels_for_action ("app.quit", {"<control>q"});

            var about_action = new SimpleAction ("about", null);
            about_action.activate.connect (() => {
                var file = File.new_for_uri ("resource:///se/sjoerd/Graphs/whats_new");
                string release_notes;
                try {
                    release_notes = (string) file.load_bytes ().get_data ();
                } catch {
                    release_notes = "";
                }

                var dialog = new Adw.AboutDialog () {
                    application_name = _("Graphs"),
                    application_icon = application_id,
                    website = Config.HOMEPAGE_URL,
                    developer_name = Config.AUTHOR,
                    issue_url = Config.ISSUE_URL,
                    version = version,
                    developers = {
                        "Sjoerd Stendahl <contact@sjoerd.se>",
                        "Christoph Matthias Kohnen <mail@cmkohnen.de>"
                    },
                    designers = {
                        "Sjoerd Stendahl <contact@sjoerd.se>",
                        "Christoph Matthias Kohnen <mail@cmkohnen.de>",
                        "Tobias Bernard <tbernard@gnome.org>"
                    },
                    copyright = "© " + Config.COPYRIGHT,
                    license_type = License.GPL_3_0,
                    translator_credits = _("translator-credits"),
                    release_notes = release_notes
                };
                dialog.present (active_window);
            });
            add_action (about_action);

            var help_action = new SimpleAction ("help", null);
            help_action.activate.connect (() => {
                try {
                    AppInfo.launch_default_for_uri (
                        "help:graphs",
                        active_window.get_display ().get_app_launch_context ()
                    );
                } catch { assert_not_reached (); }
            });
            add_action (help_action);
            set_accels_for_action ("app.help", {"F1"});

            var new_project_action = new SimpleAction ("new_project", null);
            new_project_action.activate.connect (() => {
                create_main_window ();
            });
            add_action (new_project_action);
        }

        /**
         * Activate the application.
         */
        public override void activate () {
            base.activate ();
            create_main_window ();
        }

        /**
         * Handle File Opening.
         */
        public override void open (File[] files, string hint) {
            base.open (files, hint);
            if (files.length == 1) {
                File file = files[0];
                string uri = file.get_uri ();

                if (uri.has_suffix (".graphs")) {
                    var window = create_main_window ();
                    try {
                        window.data.load (file);
                    } catch (ProjectParseError e) {
                        window.add_toast_string (e.message);
                    }
                    return;
                } else if (uri.has_suffix (".mplstyle")) {
                    create_style_editor (file);
                    return;
                }
            }

            // Import
            // try using a "clean" window
            Window? window = null;
            foreach (Window pot_window in main_windows) {
                if (!pot_window.data.unsaved && pot_window.data.file == null) {
                    window = pot_window;
                    break;
                }
            }
            if (window == null) {
                window = create_main_window ();
            }
            python_helper.import_from_files (window, files);
        }

        public Window create_main_window () {
            Window window = python_helper.create_window ();
            main_windows.add (window);
            window.present ();
            return window;
        }

        public StyleEditor create_style_editor (File file) {
            var style_editor = python_helper.create_style_editor ();
            style_editor.load (file);
            style_editors.add (style_editor);
            style_editor.present ();
            return style_editor;
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

        public void on_main_window_closed (Window window) {
            main_windows.remove (window);
            try_quit ();
        }

        public void on_style_editor_closed (StyleEditor style_editor) {
            style_editors.remove (style_editor);
            try_quit ();
        }

        private void try_quit () {
            if (main_windows.size == 0 && style_editors.size == 0) {
                quit ();
            }
        }
    }
}
