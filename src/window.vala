// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;
using Adw;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/window.ui")]
    public class Window : Adw.ApplicationWindow {

        [GtkChild]
        public unowned Button undo_button { get; }

        [GtkChild]
        public unowned Button redo_button { get; }

        [GtkChild]
        public unowned Button view_back_button { get; }

        [GtkChild]
        public unowned Button view_forward_button { get; }

        [GtkChild]
        public unowned ToggleButton pan_button { get; }

        [GtkChild]
        private unowned ToggleButton zoom_button { get; }

        [GtkChild]
        private unowned ToggleButton select_button { get; }

        [GtkChild]
        public unowned Box stack_switcher_box { get; }

        [GtkChild]
        public unowned Stack stack { get; }

        [GtkChild]
        public unowned Button shift_button { get; }

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
        public unowned ListBox item_list { get; }

        [GtkChild]
        public unowned Adw.OverlaySplitView split_view { get; }

        [GtkChild]
        private unowned Adw.ToastOverlay toast_overlay { get; }

        public int mode {
            set {
                this.pan_button.set_active (value == 0);
                this.zoom_button.set_active (value == 1);
                this.select_button.set_active (value == 2);
            }
        }

        public CanvasInterface canvas {
            get { return (CanvasInterface) this.toast_overlay.get_child (); }
            set { this.toast_overlay.set_child(value); }
        }

        [GtkCallback]
        private void perform_operation (Button button) {
            var action = this.application.lookup_action (
                "app.perform_operation"
            );
            var content = (Adw.ButtonContent) button.get_child ();
            action.activate (new Variant.string (content.get_label ()));
        }

        public void add_toast (Adw.Toast toast) {
            this.toast_overlay.add_toast (toast);
        }

        [GtkCallback]
        private void on_sidebar_toggle () {
            this.application.lookup_action ("toggle_sidebar").change_state (
                new Variant.boolean (this.split_view.get_collapsed ())
            );
        }

        public void add_toast_string (string title) {
            this.add_toast (new Adw.Toast (title));
        }
    }
}
