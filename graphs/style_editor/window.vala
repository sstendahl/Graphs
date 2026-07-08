// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gdk;

namespace Graphs {
    /**
     * Style Editor Window window
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/window.ui")]
    public class StyleEditor : Adw.ApplicationWindow {

        private const string CSS_TEMPLATE = ".canvas-view#%s {background-color: %s; color: %s; }";

        // [0, 10]
        private const double PREVIEW_XDATA[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
        // [0, e^10]
        private const double PREVIEW_YDATA1[] = {0, 2202.646579, 4405.293159, 6607.939738, 8810.586318, 11013.232897, 13215.879477, 15418.526056, 17621.172636, 19823.819215, 22026.465795};
        // [0, 5]
        private const double PREVIEW_XERR1[] = {0.1, 0.14, 0.18, 0.22, 0.26, 0.30, 0.34, 0.38, 0.42, 0.46, 0.50};
        // [500, 2500]
        private const double PREVIEW_YERR1[] = {500, 700, 900, 1100, 1300, 1500, 1700, 1900, 2100, 2300, 2500};
        // [1, e^x]
        private const double PREVIEW_YDATA2[] = {1, 2.718282, 7.389056, 20.085537, 54.598150, 148.413159, 403.428793, 1096.633158, 2980.957987, 8103.083928, 22026.465795};

        [GtkChild]
        private unowned Adw.Bin editor_bin { get; }

        [GtkChild]
        private unowned Adw.Bin canvas_bin { get; }

        [GtkChild]
        private unowned Gtk.Stack stack { get; }

        [GtkChild]
        private unowned Gtk.GridView style_grid { get; }

        [GtkChild]
        private unowned Adw.ToolbarView content_view { get; }

        protected StyleEditorBox editor_box {
            get { return (StyleEditorBox) editor_bin.get_child (); }
            set {
                editor_bin.set_child (value);
                value.notify["parameters"].connect (on_params_changed);
                reload_canvas ();
            }
        }

        protected ListStore test_items { get; private set; }
        private Gtk.CssProvider css_provider;
        private bool unsaved = false;
        private bool loading = false;
        private File _file;
        private bool _force_close = false;
        private uint _inhibit_cookie = 0;
        private string _stylename;
        private uint _reload_source = 0;

        construct {
            this.css_provider = new Gtk.CssProvider ();
            Gtk.StyleContext.add_provider_for_display (
                Display.get_default (), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            );
            content_view.set_name (Application.get_next_css_name ());

            var parameters = StyleManager.get_system_style_params ();
            test_items = new ListStore (typeof (Item));
            var test_item_a = ItemFactory.new_data_item (parameters, PREVIEW_XDATA, PREVIEW_YDATA1, PREVIEW_XERR1, PREVIEW_YERR1);
            test_item_a.name = _("Example Item");
            test_items.append (test_item_a);
            var test_item_b = ItemFactory.new_data_item (parameters, PREVIEW_XDATA, PREVIEW_YDATA2);
            test_item_b.name = _("Example Item");
            test_items.append (test_item_b);

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
                var dialog = new Gtk.FileDialog ();
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
                var dialog = new Gtk.FileDialog ();
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
                var dialog = (Adw.AlertDialog) Tools.build_dialog ("save_style_changes");
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
                unowned string path = "/se/sjoerd/Graphs/ui/style-editor/shortcuts.ui";
                var builder = new Gtk.Builder.from_resource (path);
                var shortcuts_dialog = (Adw.ShortcutsDialog) builder.get_object ("shortcuts");
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

            var factory = new Gtk.SignalListItemFactory ();
            factory.setup.connect (on_factory_setup);
            factory.bind.connect (on_factory_bind);
            style_grid.set_factory (factory);
            style_grid.set_model (new Gtk.NoSelection (StyleManager.filtered_style_model));
        }

        public void load (File file) {
            this._file = file;
            this.loading = true;
            editor_box.load (file);
            set_title (editor_box.parameters.name);
            reload_canvas ();
            stack.get_pages ().select_item (1, true);
            this.unsaved = false;
            this.loading = false;
        }

        public void save () {
            editor_box.save (_file);
            this.unsaved = false;
            if (_inhibit_cookie > 0) {
                application.uninhibit (_inhibit_cookie);
                _inhibit_cookie = 0;
            }
            var save_action = (SimpleAction) lookup_action ("save-style");
            save_action.set_enabled (false);
        }

        public void close_style () {
            this.unsaved = false;
            set_title (_("Graphs Style Editor"));
            stack.get_pages ().select_item (0, true);
        }

        private void on_factory_setup (Object object) {
            var item = (Gtk.ListItem) object;
            item.set_child (new StylePreview ());
        }

        private void on_factory_bind (Object object) {
            var item = (Gtk.ListItem) object;
            StylePreview preview = (StylePreview) item.get_child ();
            Style style = (Style) item.get_item ();
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
                    var launcher = new Gtk.FileLauncher (style.file);
                    launcher.set_always_ask (true);
                    launcher.launch.begin (this, null);
                });
                action_group.add_action (open_with_action);
                var delete_action = new SimpleAction ("delete", null);
                delete_action.activate.connect (() => {
                    var dialog = (Adw.AlertDialog) Tools.build_dialog ("delete_style");
                    unowned string msg = _("Are you sure you want to delete %s?");
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
            var application = (Application) application;

            if (_force_close) {
                application.on_style_editor_closed (this);
                return false;
            }

            if (unsaved) {
                var dialog = (Adw.AlertDialog) Tools.build_dialog ("save_style_changes");
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

        private void on_params_changed () {
            if (loading) return;

            if (_inhibit_cookie == 0) _inhibit_cookie = application.inhibit (
                this,
                Gtk.ApplicationInhibitFlags.LOGOUT,
                _stylename
            );
            var save_action = (SimpleAction) lookup_action ("save-style");
            save_action.set_enabled (true);
            this.unsaved = true;

            if (_reload_source != 0) Source.remove (_reload_source);
            _reload_source = Timeout.add_once (200, () => {
                reload_canvas ();
                _reload_source = 0;
            });
        }

        private void reload_canvas () {
            Graphs.StyleParameters style;
            if (editor_box.parameters == null) {
                style = StyleManager.get_system_style_params ();
            } else {
                style = editor_box.parameters;
                this._stylename = style.name;

                // Translators: Window title that will be formatted with the stylename.
                set_title (_("Graphs Style Editor — %s").printf (_stylename));

                if (_inhibit_cookie > 0) {
                    application.uninhibit (_inhibit_cookie);
                    _inhibit_cookie = application.inhibit (
                        this,
                        Gtk.ApplicationInhibitFlags.LOGOUT,
                        _stylename
                    );
                }
            }

            var color_cycle = style.color_cycle;
            var errorbar_cycle = style.errorbar_cycle;
            for (uint i = 0; i < test_items.get_n_items (); i++) {
                var item = (DataItem) test_items.get_item (i);

                item.color = color_cycle[i % color_cycle.length];
                item.errcolor = errorbar_cycle[i % errorbar_cycle.length];
                ItemFactory.override_item (item, style);
            }

            var canvas = PythonHelper.create_canvas (style, test_items);
            canvas.figure.set ("title", _("Title"));
            canvas.figure.set ("bottom_label", _("X Label"));
            canvas.figure.set ("left_label", _("Y Label"));

            css_provider.load_from_string (CSS_TEMPLATE.printf (content_view.get_name (), style.background_color, style.color));

            canvas_bin.set_child (canvas);
        }
    }
}
