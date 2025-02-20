// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;
using Adw;

namespace Graphs {
    /**
     * Style Editor Window window
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor-window.ui")]
    public class StyleEditor : Adw.ApplicationWindow {

        [GtkChild]
        private unowned Adw.Bin editor_bin { get; }

        [GtkChild]
        private unowned Adw.Bin canvas_bin { get; }

        [GtkChild]
        private unowned Stack stack { get; }

        [GtkChild]
        protected unowned Adw.HeaderBar content_headerbar { get; }

        protected Gtk.Box editor_box {
            get { return editor_bin.get_child () as Gtk.Box; }
            set { editor_bin.set_child (value); }
        }
        protected Canvas canvas {
            get { return canvas_bin.get_child () as Canvas; }
            set { canvas_bin.set_child (value); }
        }

        protected CssProvider headerbar_provider { get; private set; }
        protected bool unsaved { get; set; default = false; }
        private File _file;
        private bool _force_close = false;
        private uint _inhibit_cookie = 0;

        protected signal void load_request (File file);
        protected signal void save_request (File file);

        construct {
            this.headerbar_provider = new CssProvider ();
            content_headerbar.get_style_context ().add_provider (
                headerbar_provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );

            var save_action = new SimpleAction ("save-style", null);
            save_action.activate.connect (() => {
                if (_file == null) return;
                save ();
            });
            add_action (save_action);

            var save_as_action = new SimpleAction ("save-style-as", null);
            save_as_action.activate.connect (() => {
                if (_file == null) return;
                var dialog = new FileDialog ();
                dialog.set_filters (get_mplstyle_file_filters ());
                dialog.set_initial_name (_("Style") + ".mplstyle");
                dialog.save.begin (this, null, (d, response) => {
                    try {
                        _file = dialog.save.end (response);
                        save ();
                    } catch {}
                });
            });
            add_action (save_as_action);

            var open_action = new SimpleAction ("open-style", null);
            open_action.activate.connect (() => {
                if (_file != null) return;
                var dialog = new FileDialog ();
                dialog.set_filters (get_mplstyle_file_filters ());
                dialog.open.begin (this, null, (d, response) => {
                    try {
                        load (dialog.open.end (response));
                    } catch {}
                });
            });
            add_action (open_action);

            // Inhibit session end when there is unsaved data present
            notify["unsaved"].connect (() => {
                if (unsaved) {
                    application.inhibit (
                        this,
                        ApplicationInhibitFlags.LOGOUT,
                        title
                    );
                } else if (_inhibit_cookie > 0) {
                    application.uninhibit (_inhibit_cookie);
                }
            });

            string path = "/se/sjoerd/Graphs/ui/style-editor-shortcuts.ui";
            var builder = new Builder.from_resource (path);
            set_help_overlay (builder.get_object ("help_overlay") as ShortcutsWindow);
        }

        public void load (File file) {
            this._file = file;
            load_request.emit (file);
            stack.get_pages ().select_item (1, true);
        }

        public void save () {
            save_request.emit (_file);
            this.unsaved = false;
        }

        public override bool close_request () {
            var application = application as Application;

            if (_force_close) {
                application.on_style_editor_closed (this);
                return false;
            }

            if (unsaved) {
                var dialog = Tools.build_dialog ("save_style_changes") as Adw.AlertDialog;
                dialog.response.connect ((d, response) => {
                    switch (response) {
                        case "discard": {
                            _force_close = true;
                            close ();
                            break;
                        }
                        case "save": {
                            save ();
                            _force_close = true;
                            close ();
                            break;
                        }
                    }
                });
                dialog.present (this);
                return true;
            }

            application.on_style_editor_closed (this);
            return false;
        }
    }
}
