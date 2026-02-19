// SPDX-License-Identifier: GPL-3.0-or-later
using Gee;
using Gtk;

namespace Graphs {
    public class StyleColorManager : Object {
        private ListBox box;
        private ArrayList<string> colors = new ArrayList<string> ();

        public signal void colors_changed ();

        public StyleColorManager (ListBox box) {
            this.box = box;

            var drop_target = new Gtk.DropTarget (typeof (StyleItemColorRow), Gdk.DragAction.MOVE);
            drop_target.drop.connect ((drop, val, x, y) => {
                var value_row = (StyleItemColorRow?) val.get_object ();
                var target_row = (StyleItemColorRow?) box.get_row_at_y ((int) y);
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
            var row = new StyleItemColorRow (this, index, this.colors[index]);
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

                Value val = Value (typeof (StyleItemColorRow));
                val.set_object (row);

                return new Gdk.ContentProvider.for_value (val);
            });

            drag_source.drag_begin.connect ((drag) => {
                var drag_widget = new Gtk.ListBox ();
                drag_widget.set_size_request (row.get_width (), row.get_height ());
                drag_widget.add_css_class ("boxed-list");

                var drag_row = new StyleItemColorRow (this, index, this.colors[index]);

                drag_widget.append (drag_row);
                drag_widget.drag_highlight_row (drag_row);

                var icon = (Gtk.DragIcon) Gtk.DragIcon.get_for_drag (drag);
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
