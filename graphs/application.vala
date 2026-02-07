// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gdk;
using Gee;
using Gtk;

namespace Graphs {
    private const string[] X_DIRECTIONS = {"top", "bottom"};
    private const string[] Y_DIRECTIONS = {"left", "right"};

    /**
     * Graphs application
     */
    public class Application : Adw.Application {
        public GLib.Settings settings { get; private set; }
        public StyleManager figure_style_manager { get; protected set; }

        private Gee.List<Window> main_windows;
        private Gee.List<StyleEditor> style_editors;
        private uint _css_counter = 0;

        private const OptionEntry[] OPTION_ENTRIES = {
            { "version", 0, 0, OptionArg.NONE, null, "Display version number", null },
            { "new-window", 'n', 0, OptionArg.NONE, null, "New window", null },
            { "style-editor", 's', 0, OptionArg.NONE, null, "Style Editor", null },
            { null },
        };

        construct {
            Intl.bindtextdomain (Config.GETTEXT_PACKAGE, Config.LOCALEDIR);
            Intl.bind_textdomain_codeset (Config.GETTEXT_PACKAGE, "UTF-8");
            Intl.textdomain (Config.GETTEXT_PACKAGE);

            this.main_windows = new Gee.LinkedList<Window> ();
            this.style_editors = new Gee.LinkedList<StyleEditor> ();

            this.version = Config.VERSION;
            this.settings = new GLib.Settings (application_id);

            add_main_option_entries (OPTION_ENTRIES);
        }

        /**
         * Setup the application.
         */
        public override void startup () {
            base.startup ();

            Gtk.Window.set_default_icon_name (application_id);

            Actions.setup_global (this);
        }

        /**
         * Activate the application.
         */
        public override void activate () {
            base.activate ();
            var window = main_windows.is_empty ? create_main_window () : main_windows[0];
            window.present ();
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
                    window.present ();
                    Project.load.begin (window, window.data, file);
                    return;
                } else if (uri.has_suffix (".mplstyle")) {
                    var style_editor = create_style_editor ();
                    style_editor.load (file);
                    style_editor.present ();
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
            window.present ();

            var settings_list = new GLib.ListStore (typeof (ImportSettings));
            for (uint i = 0; i < files.length; i++) {
                settings_list.append (DataImporter.get_settings_for_file (files[i]));
            }
            new ImportDialog (window, settings_list);
        }

        /*
         * Handle command line
         */
        public override int command_line (ApplicationCommandLine command_line) {
            string[] args = command_line.get_arguments ();
            VariantDict options = command_line.get_options_dict ();
            File[] files = {};

            bool version;
            options.lookup ("version", "b", out version);
            if (version) {
                command_line.print ("Graphs Version %s\n", Config.VERSION);
                return 0;
            }

            for (int i = 1; i < args.length; i++) {
                string filename = args[i];
                files += command_line.create_file_for_arg (filename);
            }

            bool new_window;
            options.lookup ("new-window", "b", out new_window);
            bool new_style_editor;
            options.lookup ("style-editor", "b", out new_style_editor);

            if (files.length > 0) {
                open (files, "");
            } else if (new_window) {
                var window = create_main_window ();
                window.present ();
            } else if (new_style_editor) {
                var style_editor = create_style_editor ();
                style_editor.present ();
            } else {
                activate ();
            }
            return 0;
        }

        public Window create_main_window () {
            Window window = PythonHelper.create_window ();
            main_windows.add (window);
            return window;
        }

        public StyleEditor create_style_editor () {
            var style_editor = PythonHelper.create_style_editor ();
            style_editors.add (style_editor);
            return style_editor;
        }

        public uint get_next_css_counter () {
            _css_counter++;
            return _css_counter;
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

        public void quit_action () {
            // We need to cast to array here as the list size might change
            // during iteration
            foreach (Window window in main_windows.to_array ()) {
                window.close ();
            }
            foreach (StyleEditor style_editor in style_editors.to_array ()) {
                style_editor.close ();
            }
        }
    }
}
