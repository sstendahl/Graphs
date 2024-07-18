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
        public unowned Button cut_button { get; }

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

        public int mode {
            set {
                this.pan_button.set_active (value == 0);
                this.zoom_button.set_active (value == 1);
                this.select_button.set_active (value == 2);
            }
        }

        public Canvas canvas {
            get { return (Canvas) this.toast_overlay.get_child (); }
            set {
                value.bind_property ("mode", this, "mode", 2);
                this.toast_overlay.set_child (value);
                value.grab_focus ();
            }
        }

        public Window (Application application) {
            Object (application: application);
            Data data = application.data;
            data.bind_property (
                "items_selected", this.shift_button, "sensitive", 2
            );
            data.bind_property ("can_undo", this.undo_button, "sensitive", 2);
            data.bind_property ("can_redo", this.redo_button, "sensitive", 2);
            data.bind_property ("can_view_back", this.view_back_button, "sensitive", 2);
            data.bind_property ("can_view_forward", this.view_forward_button, "sensitive", 2);
            data.bind_property ("project_name", this.content_title, "title", 2);
            data.bind_property ("project_path", this.content_title, "subtitle", 2);

            InlineStackSwitcher stack_switcher = new InlineStackSwitcher ();
            stack_switcher.stack = this.stack;
            stack_switcher.add_css_class ("compact");
            stack_switcher.set_hexpand (true);
            this.stack_switcher_box.prepend (stack_switcher);

            string[] action_names = {
                "multiply_x",
                "multiply_y",
                "translate_x",
                "translate_y"
            };
            foreach (string action_name in action_names) {
                Entry entry;
                Button button;
                this.get (action_name + "_entry", out entry);
                this.get (action_name + "_button", out button);
                entry.notify["text"].connect (() => {
                    this.validate_entry (application, entry, button);
                });
                data.notify["items-selected"].connect (() => {
                    this.validate_entry (application, entry, button);
                });
                this.validate_entry (application, entry, button);
            }

            data.items_changed.connect (() => {
                this.item_list.set_visible (!data.is_empty ());
                this.update_view_menu ();
                data.add_view_history_state ();
            });
            this.item_list.bind_model (data, (object) => {
                return new ItemBox ((Application) this.application, (Item) object);

            });

            data.notify.connect (() => {
                this.set_dnd();
            });
            this.close_request.connect (() => {
                return application.close ();
            });

            this.update_view_menu ();
            if (application.debug) {
                this.add_css_class ("devel");
                this.set_title (_("Graphs (Development)"));
            }
        }

        private void validate_entry (Application application, Entry entry, Button button) {
            if (application.python_helper.validate_input (entry.get_text ())) {
                entry.remove_css_class ("error");
                button.set_sensitive (application.data.items_selected);
            } else {
                entry.add_css_class ("error");
                button.set_sensitive (false);
            }
        }

        [GtkCallback]
        private void perform_operation (Button button) {
            var action = this.application.lookup_action (
                "app.perform_operation"
            );
            string name = button.get_buildable_id ()[0:-7];
            action.activate (new Variant.string (name));
        }

        /**
         * Add a toast to the window.
         */
        public void add_toast (Adw.Toast toast) {
            this.toast_overlay.add_toast (toast);
        }

        /**
         * Add a toast to the window.
         *
         * The toast is created automatically with the given title.
         */
        public void add_toast_string (string title) {
            this.add_toast (new Adw.Toast (title));
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
            this.application.add_action (action);
            this.add_toast (new Adw.Toast (title) {
                button_label = _("Open Location"),
                action_name = "app.open-file-location"
            });
        }

        /**
         * Add Toast with undo action.
         */
        public void add_undo_toast (string title) {
            this.add_toast (new Adw.Toast (title) {
                button_label = _("Undo"),
                action_name = "app.undo"
            });
        }

        [GtkCallback]
        private void on_sidebar_toggle () {
            this.application.lookup_action ("toggle_sidebar").change_state (
                new Variant.boolean (this.split_view.get_collapsed ())
            );
        }

        public void set_dnd () {
            var drop_target = new Gtk.DropTarget(typeof (Adw.ActionRow), Gdk.DragAction.MOVE);
            Application application = (Application) this.application;
            Data data = application.data;
            this.item_list.add_controller(drop_target);

            for (int i = 0; this.item_list.get_row_at_index(i) != null; i++) {
                var row = this.item_list.get_row_at_index(i) as ItemBox;
                double drag_x = 0.0;
                double drag_y = 0.0;

                var drop_controller = new Gtk.DropControllerMotion();
                var drag_source = new Gtk.DragSource() {
                    actions = Gdk.DragAction.MOVE
                };

                row.add_controller(drag_source);
                row.add_controller(drop_controller);

                // Drag handling
                drag_source.prepare.connect((x, y) => {
                    drag_x = x;
                    drag_y = y;

                    Value value = Value(typeof (Adw.ActionRow));
                    value.set_object(row);

                    return new Gdk.ContentProvider.for_value(value);
                });

                drag_source.drag_begin.connect((drag) => {
                    var drag_widget = new Gtk.ListBox();
                    drag_widget.set_size_request(row.get_width(), row.get_height());
                    drag_widget.add_css_class("boxed-list");

                    var drag_row = new ItemBox ((Application) this.application, (Item) row.item){
                        title = row.get_title()
                    };

                    drag_widget.append(drag_row);
                    drag_widget.drag_highlight_row(drag_row);

                    var icon = Gtk.DragIcon.get_for_drag(drag) as Gtk.DragIcon;
                    icon.child = drag_widget;

                    drag.set_hotspot((int) drag_x, (int) drag_y);
                });

                // Update row visuals during DnD operation
                drop_controller.enter.connect(() => this.item_list.drag_highlight_row(row));
                drop_controller.leave.connect(() => this.item_list.drag_unhighlight_row());
            }


            // Drop Handling
            drop_target.drop.connect((drop, value, x, y) => {
                var value_row = value.get_object() as ItemBox ? ;
                Gtk.ListBoxRow? target_row = this.item_list.get_row_at_y((int) y);
                // If value or the target row is null, do not accept the drop
                if (value_row == null || target_row == null) {
                    return false;
                }

                int target_index = target_row.get_index();
                int source_index = value_row.get_index();


                this.item_list.remove(value_row);
                this.item_list.insert(value_row, target_index);
                data.change_position (target_index, source_index);
                data.add_history_state ();
                data.add_view_history_state ();
                target_row.set_state_flags(Gtk.StateFlags.NORMAL, true);

                return true;
            });
        }

        /**
         * Repopulate the view menu
         */
        public void update_view_menu () {
            var view_menu = new Menu ();
            var toggle_section = new Menu ();
            toggle_section.append_item (
                new MenuItem (_("Toggle Sidebar"), "app.toggle_sidebar")
            );
            view_menu.append_section (null, toggle_section);
            Menu optimize_section = new Menu ();
            optimize_section.append_item (
                new MenuItem (_("Optimize Limits"), "app.optimize_limits")
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
            Application application = (Application) this.application;
            bool[] visible_axes = application.data.get_used_positions ();
            bool both_x = visible_axes[0] && visible_axes[1];
            bool both_y = visible_axes[2] && visible_axes[3];
            for (int i = 0; i < DIRECTION_NAMES.length; i++) {
                if (!visible_axes[i]) continue;
                string direction = DIRECTION_NAMES[i];
                Menu scale_section = new Menu ();
                for (int j = 0; j < scale_names.length; j++) {
                    string scale = scale_names[j];
                    MenuItem scale_item = new MenuItem (
                        scale, @"app.change-$direction-scale"
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
            this.view_menu_button.set_menu_model (view_menu);
        }
    }
}