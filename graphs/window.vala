// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;
using Adw;

namespace Graphs {
    /**
     * Main window
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/window.ui")]
    public class Window : Adw.ApplicationWindow {

        [GtkChild]
        private unowned Button undo_button { get; }

        [GtkChild]
        private unowned Button redo_button { get; }

        [GtkChild]
        private unowned Button view_back_button { get; }

        [GtkChild]
        private unowned Button view_forward_button { get; }

        [GtkChild]
        private unowned MenuButton view_menu_button { get; }

        [GtkChild]
        private unowned ToggleButton pan_button { get; }

        [GtkChild]
        private unowned ToggleButton zoom_button { get; }

        [GtkChild]
        private unowned ToggleButton select_button { get; }

        [GtkChild]
        private unowned Box stack_switcher_box { get; }

        [GtkChild]
        private unowned Stack stack { get; }

        [GtkChild]
        private unowned Button shift_button { get; }

        [GtkChild]
        protected unowned Button cut_button { get; }

        [GtkChild]
        public unowned Entry translate_x_entry { get; }

        [GtkChild]
        public unowned Entry translate_y_entry { get; }

        [GtkChild]
        public unowned Entry multiply_x_entry { get; }

        [GtkChild]
        public unowned Entry multiply_y_entry { get; }

        [GtkChild]
        public unowned Button translate_x_button { get; }

        [GtkChild]
        public unowned Button translate_y_button { get; }

        [GtkChild]
        public unowned Button multiply_x_button { get; }

        [GtkChild]
        public unowned Button multiply_y_button { get; }

        [GtkChild]
        private unowned ListBox item_list { get; }

        [GtkChild]
        public unowned Adw.OverlaySplitView split_view { get; }

        [GtkChild]
        private unowned Adw.ToastOverlay toast_overlay { get; }

        [GtkChild]
        private unowned Adw.HeaderBar content_headerbar { get; }

        [GtkChild]
        private unowned Adw.WindowTitle content_title { get; }

        public Data data { get; construct set; }

        protected CssProvider headerbar_provider { get; private set; }

        public int mode {
            set {
                pan_button.set_active (value == 0);
                zoom_button.set_active (value == 1);
                select_button.set_active (value == 2);
            }
        }

        public Canvas canvas {
            get { return toast_overlay.get_child () as Canvas; }
            set {
                value.bind_property ("mode", this, "mode", 2);
                toast_overlay.set_child (value);
                value.grab_focus ();
            }
        }

        private bool _force_close = false;
        private uint _inhibit_cookie = 0;

        construct {
            InlineStackSwitcher stack_switcher = new InlineStackSwitcher ();
            stack_switcher.stack = stack;
            stack_switcher.add_css_class ("compact");
            stack_switcher.set_hexpand (true);
            stack_switcher_box.prepend (stack_switcher);

            this.headerbar_provider = new CssProvider ();
            content_headerbar.get_style_context ().add_provider (
                headerbar_provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );

            var drop_target = new Gtk.DropTarget (typeof (Adw.ActionRow), Gdk.DragAction.MOVE);
            drop_target.drop.connect ((drop, val, x, y) => {
                var value_row = val.get_object () as ItemBox?;
                var target_row = item_list.get_row_at_y ((int) y) as ItemBox?;
                // If value or the target row is null, do not accept the drop
                if (value_row == null || target_row == null) {
                    return false;
                }

                target_row.change_position (value_row.get_index ());
                target_row.set_state_flags (Gtk.StateFlags.NORMAL, true);

                return true;
            });
            item_list.add_controller (drop_target);

            string path = "/se/sjoerd/Graphs/ui/window-shortcuts.ui";
            var builder = new Builder.from_resource (path);
            set_help_overlay (builder.get_object ("help_overlay") as ShortcutsWindow);
        }

        protected void setup () {
            var application = application as Application;

            Actions.setup (application, this);

            data.bind_property ("items_selected", shift_button, "sensitive", 2);
            data.bind_property ("can_undo", undo_button, "sensitive", 2);
            data.bind_property ("can_redo", redo_button, "sensitive", 2);
            data.bind_property ("can_view_back", view_back_button, "sensitive", 2);
            data.bind_property ("can_view_forward", view_forward_button, "sensitive", 2);
            data.bind_property ("project_name", content_title, "title", 2);
            data.bind_property ("project_path", content_title, "subtitle", 2);

            string[] action_names = {
                "multiply_x",
                "multiply_y",
                "translate_x",
                "translate_y"
            };
            foreach (string action_name in action_names) {
                Entry entry;
                Button button;
                get (action_name + "_entry", out entry);
                get (action_name + "_button", out button);
                entry.notify["text"].connect (() => {
                    validate_entry (entry, button);
                });
                data.notify["items-selected"].connect (() => {
                    validate_entry (entry, button);
                });
                validate_entry (entry, button);
            }

            data.items_changed.connect (() => {
                item_list.set_visible (!data.is_empty ());
                update_view_menu ();
                reload_item_list ();
                data.add_view_history_state ();
            });
            // Inhibit session end when there is unsaved data present
            data.notify["unsaved"].connect (() => {
                if (data.unsaved) {
                    application.inhibit (
                        this,
                        ApplicationInhibitFlags.LOGOUT,
                        data.project_name
                    );
                } else if (_inhibit_cookie > 0) {
                    application.uninhibit (_inhibit_cookie);
                }
            });

            update_view_menu ();
            if (application.debug) {
                add_css_class ("devel");
                set_title (_("Graphs (Development)"));
            }
        }

        private void reload_item_list () {
            item_list.remove_all ();
            uint index = 0;
            foreach (Item item in data) {
                var row = new ItemBox (this, item, index);
                row.setup_interactions ();

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

                    Value val = Value (typeof (Adw.ActionRow));
                    val.set_object (row);

                    return new Gdk.ContentProvider.for_value (val);
                });

                drag_source.drag_begin.connect ((drag) => {
                    var drag_widget = new Gtk.ListBox ();
                    drag_widget.set_size_request (row.get_width (), row.get_height ());
                    drag_widget.add_css_class ("boxed-list");

                    var drag_row = new ItemBox (this, item, index);

                    drag_widget.append (drag_row);
                    drag_widget.drag_highlight_row (drag_row);

                    var icon = Gtk.DragIcon.get_for_drag (drag) as Gtk.DragIcon;
                    icon.child = drag_widget;

                    drag.set_hotspot ((int) drag_x, (int) drag_y);
                });

                // Update row visuals during DnD operation
                drop_controller.enter.connect (() => item_list.drag_highlight_row (row));
                drop_controller.leave.connect (() => item_list.drag_unhighlight_row ());

                item_list.append (row);
                index++;
            }
        }

        private void validate_entry (Entry entry, Button button) {
            var application = application as Application;
            double? val = application.python_helper.evaluate_string (entry.get_text ());
            if (val == null) {
                entry.add_css_class ("error");
                button.set_sensitive (false);
            } else {
                entry.remove_css_class ("error");
                button.set_sensitive (data.items_selected);
            }
        }

        [GtkCallback]
        private void perform_operation (Button button) {
            var action = this.lookup_action (
                "perform_operation"
            );
            string name = button.get_buildable_id ()[0:-7];
            action.activate (new Variant.string (name));
        }

        /**
         * Add a toast to the window.
         */
        public void add_toast (Adw.Toast toast) {
            toast_overlay.add_toast (toast);
        }

        /**
         * Add a toast to the window.
         *
         * The toast is created automatically with the given title.
         */
        public void add_toast_string (string title) {
            add_toast (new Adw.Toast (title));
        }

        /**
         * Add a toast to the window.
         *
         * The toast is created automatically with the given title.
         * An action is automatically created, to open the containing folder
         * of file.
         */
        public void add_toast_string_with_file (string title, File file) {
            SimpleAction action = new SimpleAction ("open-file-location", null);
            action.activate.connect (() => {
                Tools.open_file_location (file);
            });
            add_action (action);
            add_toast (new Adw.Toast (title) {
                button_label = _("Open Location"),
                action_name = "win.open-file-location"
            });
        }

        /**
         * Add Toast with undo action.
         */
        public void add_undo_toast (string title) {
            add_toast (new Adw.Toast (title) {
                button_label = _("Undo"),
                action_name = "win.undo"
            });
        }

        [GtkCallback]
        private void on_sidebar_toggle () {
            application.lookup_action ("toggle_sidebar").change_state (
                new Variant.boolean (split_view.get_collapsed ())
            );
        }

        /**
         * Repopulate the view menu
         */
        public void update_view_menu () {
            var view_menu = new Menu ();
            var toggle_section = new Menu ();
            toggle_section.append_item (
                new MenuItem (_("Toggle Sidebar"), "win.toggle_sidebar")
            );
            view_menu.append_section (null, toggle_section);
            Menu optimize_section = new Menu ();
            optimize_section.append_item (
                new MenuItem (_("Optimize Limits"), "win.optimize_limits")
            );
            view_menu.append_section (null, optimize_section);

            string[] scale_names = {
                C_("scale", "Linear"),
                C_("scale", "Logarithmic"),
                C_("scale", "Radians"),
                C_("scale", "Square Root"),
                C_("scale", "Inverse Root")
            };

            Menu scales_section = new Menu ();
            bool[] visible_axes = data.get_used_positions ();
            bool both_x = visible_axes[0] && visible_axes[1];
            bool both_y = visible_axes[2] && visible_axes[3];
            for (int i = 0; i < DIRECTION_NAMES.length; i++) {
                if (!visible_axes[i]) continue;
                string direction = DIRECTION_NAMES[i];
                Menu scale_section = new Menu ();
                for (int j = 0; j < scale_names.length; j++) {
                    string scale = scale_names[j];
                    MenuItem scale_item = new MenuItem (
                        scale, @"win.change-$direction-scale"
                    );
                    scale_item.set_attribute_value (
                        "target",
                        new Variant.string (j.to_string ())
                    );
                    scale_section.append_item (scale_item);
                }
                string label;
                if (i < 2) {
                    if (both_x) {
                        if (i == 0) label = _("Bottom X Axis Scale");
                        else label = _("Top X Axis Scale");
                    } else label = _("X Axis Scale");
                } else {
                    if (both_y) {
                        if (i == 3) label = _("Right Y Axis Scale");
                        else label = _("Left Y Axis Scale");
                    } else label = _("Y Axis Scale");
                }
                scales_section.append_submenu (label, scale_section);
            }
            view_menu.append_section (null, scales_section);
            view_menu_button.set_menu_model (view_menu);
        }

        public override bool close_request () {
            var application = application as Application;

            if (_force_close) {
                application.on_main_window_closed (this);
                return false;
            }

            if (data.unsaved) {
                var dialog = Tools.build_dialog ("save_project_changes") as Adw.AlertDialog;
                dialog.response.connect ((d, response) => {
                    switch (response) {
                        case "discard": {
                            _force_close = true;
                            close ();
                            break;
                        }
                        case "save": {
                            Project.save.begin (this, false, (o, result) => {
                                if (Project.save.end (result)) {
                                    _force_close = true;
                                    close ();
                                }
                            });
                            break;
                        }
                    }
                });
                dialog.present (this);
                return true;
            }
            application.on_main_window_closed (this);
            return false;
        }
    }
}
