// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gdk;
using Gtk;

namespace Graphs {
    /**
     * Style Editor Window window
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/window.ui")]
    public class StyleEditor : Adw.ApplicationWindow {

        [GtkChild]
        private unowned Adw.Bin editor_bin { get; }

        [GtkChild]
        private unowned Adw.Bin canvas_bin { get; }

        [GtkChild]
        private unowned Stack stack { get; }

        [GtkChild]
        private unowned GridView style_grid { get; }

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

        construct {
            this.css_provider = new CssProvider ();
            StyleContext.add_provider_for_display (
                Display.get_default (), css_provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );

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
                            var new_window = ((Application) application).create_style_editor ();
                            new_window.load (file);
                            new_window.present ();
                        }
                    } catch {}
                });
            });
            add_action (open_action);

            var close_action = new SimpleAction ("close-style", null);
            close_action.activate.connect (() => {
                if (!unsaved) {
                    close_style ();
                    return;
                }
                var dialog = Tools.build_dialog ("save_style_changes") as Adw.AlertDialog;
                dialog.response.connect ((d, response) => {
                    switch (response) {
                        case "discard": {
                            close_style ();
                            break;
                        }
                        case "save": {
                            save ();
                            close_style ();
                            break;
                        }
                    }
                });
                dialog.present (this);
            });
            add_action (close_action);

            var show_shortcuts_action = new SimpleAction ("show-shortcuts", null);
            show_shortcuts_action.activate.connect (() => {
                string path = "/se/sjoerd/Graphs/ui/style-editor/shortcuts.ui";
                var builder = new Builder.from_resource (path);
                var shortcuts_dialog = builder.get_object ("shortcuts") as Adw.ShortcutsDialog;
                shortcuts_dialog.present (this);
            });
            add_action (show_shortcuts_action);

            var import_action = new SimpleAction ("import-style", null);
            import_action.activate.connect (() => {
                import_style.begin (this);
            });
            add_action (import_action);

            var create_action = new SimpleAction ("create-style", null);
            create_action.activate.connect (() => {
                var dialog = new AddStyleDialog (this);
                dialog.accept.connect ((file) => {
                    load (file);
                });
            });
            add_action (create_action);

             // Inhibit session end when there is unsaved data present
            notify["unsaved"].connect (() => {
                if (unsaved) {
                    if (_inhibit_cookie == 0) _inhibit_cookie = application.inhibit (
                        this,
                        ApplicationInhibitFlags.LOGOUT,
                        _stylename
                    );
                    save_action.set_enabled (true);
                } else {
                    if (_inhibit_cookie > 0) {
                        application.uninhibit (_inhibit_cookie);
                        _inhibit_cookie = 0;
                    }
                    save_action.set_enabled (false);
                }
            });

            var factory = new SignalListItemFactory ();
            factory.setup.connect (on_factory_setup);
            factory.bind.connect (on_factory_bind);
            style_grid.set_factory (factory);
        }

        protected void setup () {
            var model = new NoSelection (StyleManager.filtered_style_model);
            style_grid.set_model (model);
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

        public void close_style () {
            this.unsaved = false;
            set_title (_("Graphs Style Editor"));
            stack.get_pages ().select_item (0, true);
        }

        private void on_factory_setup (Object object) {
            ListItem item = object as ListItem;
            item.set_child (new StylePreview ());
        }

        private void on_factory_bind (Object object) {
            ListItem item = object as ListItem;
            StylePreview preview = item.get_child () as StylePreview;
            Style style = item.get_item () as Style;
            preview.style = style;
            if (style.mutable && !preview.menu_button.get_visible ()) {
                preview.menu_button.set_visible (true);

                var action_group = new SimpleActionGroup ();
                var open_action = new SimpleAction ("open", null);
                open_action.activate.connect (() => {
                    load (style.file);
                });
                action_group.add_action (open_action);
                var open_with_action = new SimpleAction ("open_with", null);
                open_with_action.activate.connect (() => {
                    var launcher = new FileLauncher (style.file);
                    launcher.set_always_ask (true);
                    launcher.launch.begin (this, null);
                });
                action_group.add_action (open_with_action);
                var delete_action = new SimpleAction ("delete", null);
                delete_action.activate.connect (() => {
                    var dialog = Tools.build_dialog ("delete_style") as Adw.AlertDialog;
                    string msg = _("Are you sure you want to delete %s?");
                    dialog.set_body (msg.printf (style.name));
                    dialog.response.connect ((d, response) => {
                        if (response != "delete") return;
                        try {
                            style.file.trash ();
                        } catch {
                            assert_not_reached ();
                        }
                    });
                    dialog.present (this);
                });
                action_group.add_action (delete_action);
                preview.menu_button.insert_action_group ("style", action_group);
            }
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
