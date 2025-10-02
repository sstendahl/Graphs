// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gdk;
using Gee;
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

            var show_shortcuts_action = new SimpleAction ("show-shortcuts", null);
            show_shortcuts_action.activate.connect (() => {
                string path = "/se/sjoerd/Graphs/ui/style-editor/shortcuts.ui";
                var builder = new Builder.from_resource (path);
                var shortcuts_dialog = builder.get_object ("shortcuts") as Adw.ShortcutsDialog;
                shortcuts_dialog.present (this);
            });
            add_action (show_shortcuts_action);

            var import_action = new SimpleAction ("import_style", null);
            import_action.activate.connect (() => {
                var application = (Application) application;
                import_style.begin (this, application.figure_style_manager);
            });
            add_action (import_action);

            var create_action = new SimpleAction ("create_style", null);
            create_action.activate.connect (() => {
                var application = (Application) application;
                var dialog = new AddStyleDialog (application.figure_style_manager, this);
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
            var application = (Application) application;

            var model = new NoSelection (application.figure_style_manager.style_model);
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

    /**
     * Style Color Box
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/color-box.ui")]
    public class StyleColorBox : Adw.ActionRow {
        public int index { get; construct set; }

        [GtkChild]
        private unowned Gtk.Button color_button { get; }

        private CssProvider provider = new CssProvider ();
        private string color;
        public StyleColorManager color_manager;

        public signal void color_changed (string color);
        public signal void color_removed ();

        construct {
            this.color_button.get_style_context ().add_provider (
                this.provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );
        }

        public StyleColorBox (StyleColorManager color_manager, int index, string color) {
            Object (index: index);
            this.set_title (_("Color %d").printf (index + 1));
            this.color_manager = color_manager;
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

    public class StyleColorManager : Object {
        private ListBox box;
        private ArrayList<string> colors = new ArrayList<string> ();

        public signal void colors_changed ();

        public StyleColorManager (ListBox box) {
            this.box = box;

            var drop_target = new Gtk.DropTarget (typeof (StyleColorBox), Gdk.DragAction.MOVE);
            drop_target.drop.connect ((drop, val, x, y) => {
                var value_row = val.get_object () as StyleColorBox?;
                var target_row = box.get_row_at_y ((int) y) as StyleColorBox?;
                // If value or the target row is null, do not accept the drop
                if (value_row == null || target_row == null) return false;

                // Reject if the value row is not from this instance
                if (value_row.color_manager != this) return false;

                change_position (target_row.index, value_row.index);
                target_row.set_state_flags (Gtk.StateFlags.NORMAL, true);

                return true;
            });
            box.add_controller (drop_target);
        }

        public void set_colors (string[] colors) {
            this.colors.clear ();
            this.colors.add_all_array (colors);
            reload_color_boxes ();
        }

        public void add_color (string color) {
            this.colors.add (color);
            append_style_color_box (this.colors.size - 1);
            colors_changed.emit ();
        }

        public string[] get_colors () {
            return this.colors.to_array ();
        }

        public void change_position (int index1, int index2) {
            if (index1 == index2) return;
            string color = this.colors[index2];
            this.colors.remove_at (index2);
            this.colors.insert (index1, color);
            reload_color_boxes ();
            colors_changed.emit ();
        }

        private void append_style_color_box (int index) {
            var row = new StyleColorBox (this, index, this.colors[index]);
            row.color_removed.connect (() => {
                this.colors.remove_at (index);
                reload_color_boxes ();
                colors_changed.emit ();
            });
            row.color_changed.connect ((b, color) => {
                this.colors[index] = color;
                colors_changed.emit ();
            });

            double drag_x = 0.0;
            double drag_y = 0.0;

            var drop_controller = new Gtk.DropControllerMotion ();
            var drag_source = new Gtk.DragSource () {
                actions = Gdk.DragAction.MOVE
            };

            row.add_controller (drag_source);
            row.add_controller (drop_controller);

            // Drag handling
            drag_source.prepare.connect ((x, y) => {
                drag_x = x;
                drag_y = y;

                Value val = Value (typeof (StyleColorBox));
                val.set_object (row);

                return new Gdk.ContentProvider.for_value (val);
            });

            drag_source.drag_begin.connect ((drag) => {
                var drag_widget = new Gtk.ListBox ();
                drag_widget.set_size_request (row.get_width (), row.get_height ());
                drag_widget.add_css_class ("boxed-list");

                var drag_row = new StyleColorBox (this, index, this.colors[index]);

                drag_widget.append (drag_row);
                drag_widget.drag_highlight_row (drag_row);

                var icon = Gtk.DragIcon.get_for_drag (drag) as Gtk.DragIcon;
                icon.child = drag_widget;

                drag.set_hotspot ((int) drag_x, (int) drag_y);
            });

            // Update row visuals during DnD operation
            drop_controller.enter.connect (() => this.box.drag_highlight_row (row));
            drop_controller.leave.connect (() => this.box.drag_unhighlight_row ());

            this.box.append (row);
        }

        private void reload_color_boxes () {
            if (this.colors.is_empty) this.colors.add ("#000000");
            this.box.remove_all ();
            for (int i = 0; i < this.colors.size; i++) {
                append_style_color_box (i);
            }
        }
    }
}
