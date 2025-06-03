// SPDX-License-Identifier: GPL-3.0-or-later
using Gdk;
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
        protected unowned Adw.ToolbarView content_view { get; }

        protected Gtk.Box editor_box {
            get { return editor_bin.get_child () as Gtk.Box; }
            set { editor_bin.set_child (value); }
        }
        protected Canvas canvas {
            get { return canvas_bin.get_child () as Canvas; }
            set { canvas_bin.set_child (value); }
        }
        protected string stylename {
            set {
                this._stylename = value;
                // Translators: Window title that will be formatted with the stylename.
                set_title (_("Graphs Style Editor — %s").printf (value));

                if (_inhibit_cookie > 0) {
                    application.uninhibit (_inhibit_cookie);
                    _inhibit_cookie = application.inhibit (
                        this,
                        ApplicationInhibitFlags.LOGOUT,
                        value
                    );
                }
            }
        }

        protected CssProvider css_provider { get; private set; }
        protected bool unsaved { get; set; default = false; }
        private File _file;
        private bool _force_close = false;
        private uint _inhibit_cookie = 0;
        private string _stylename;

        protected signal void load_request (File file);
        protected signal void save_request (File file);

        protected void setup () {
            var application = application as Application;

            this.css_provider = new CssProvider ();
            StyleContext.add_provider_for_display (
                Display.get_default (), css_provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );
            content_view.set_name ("view" + application.get_next_css_counter ().to_string ());

            var save_action = new SimpleAction ("save-style", null);
            save_action.activate.connect (() => {
                if (_file == null) return;
                save ();
            });
            save_action.set_enabled (false);
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
                var dialog = new FileDialog ();
                dialog.set_filters (get_mplstyle_file_filters ());
                dialog.open.begin (this, null, (d, response) => {
                    try {
                        var file = dialog.open.end (response);
                        if (_file == null || !unsaved) {
                            load (file);
                        } else {
                            var new_window = application.create_style_editor ();
                            new_window.load (file);
                            new_window.present ();
                        }
                    } catch {}
                });
            });
            add_action (open_action);

            // Inhibit session end when there is unsaved data present
            notify["unsaved"].connect (() => {
                if (unsaved) {
                    _inhibit_cookie = application.inhibit (
                        this,
                        ApplicationInhibitFlags.LOGOUT,
                        _stylename
                    );
                    save_action.set_enabled (true);
                } else {
                    if (_inhibit_cookie > 0) application.uninhibit (_inhibit_cookie);
                    save_action.set_enabled (false);
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

    /**
     * Style Color Box
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-color-box.ui")]
    public class StyleColorBox : Gtk.Box {

        [GtkChild]
        private unowned Gtk.Label label { get; }

        [GtkChild]
        private unowned Gtk.Button color_button { get; }

        private CssProvider provider = new CssProvider ();
        private string color;

        public signal void color_changed (string color);
        public signal void color_removed ();

        construct {
            this.color_button.get_style_context ().add_provider (
                this.provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );
        }

        public StyleColorBox (int index, string color) {
            this.label.set_label (_("Color %d").printf (index + 1));
            this.color = color;
            load_color ();
        }

        private void load_color () {
            this.provider.load_from_string (@"button { color: $color; }");
        }

        [GtkCallback]
        private void on_color_choose () {
            var dialog = new ColorDialog () { with_alpha = false };
            dialog.choose_rgba.begin (
                this.get_root () as Gtk.Window,
                Tools.hex_to_rgba (color),
                null,
                (d, result) => {
                    try {
                        color = Tools.rgba_to_hex (dialog.choose_rgba.end (result));
                        load_color ();
                        color_changed.emit (color);
                    } catch {}

                }
            );
        }

        [GtkCallback]
        private void on_delete () {
            color_removed.emit ();
        }
    }
}
