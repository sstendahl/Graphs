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
        public unowned MenuButton view_menu_button { get; }

        [GtkChild]
        public unowned ToggleButton pan_button { get; }

        [GtkChild]
        private unowned ToggleButton zoom_button { get; }

        [GtkChild]
        private unowned ToggleButton select_button { get; }

        [GtkChild]
        private unowned Box stack_switcher_box { get; }

        [GtkChild]
        private unowned Stack stack { get; }

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
        public unowned Button translate_x_button { get; }

        [GtkChild]
        public unowned Button translate_y_button { get; }

        [GtkChild]
        public unowned Button multiply_x_button { get; }

        [GtkChild]
        public unowned Button multiply_y_button { get; }

        [GtkChild]
        public unowned ListBox item_list { get; }

        [GtkChild]
        public unowned Adw.OverlaySplitView split_view { get; }

        [GtkChild]
        private unowned Adw.ToastOverlay toast_overlay { get; }

        [GtkChild]
        private unowned Adw.HeaderBar content_headerbar { get; }

        [GtkChild]
        public unowned Adw.WindowTitle content_title { get; }

        [GtkChild]
        public unowned EventControllerKey key_controller { get; }

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

        public CssProvider headerbar_provider { get; private set; }

        public Window (Application application) {
            Object (application: application);
            DataInterface data = application.data;
            data.bind_property (
                "items_selected", this.shift_button, "sensitive", 2
            );
            data.bind_property ("empty", this.item_list, "visible", 4);
            application.bind_property ("mode", this, "mode", 2);

            InlineStackSwitcher stack_switcher = new InlineStackSwitcher ();
            stack_switcher.stack = this.stack;
            stack_switcher.add_css_class ("compact");
            stack_switcher.set_hexpand (true);
            this.stack_switcher_box.prepend (stack_switcher);

            this.headerbar_provider = new CssProvider ();
            StyleContext context = this.content_headerbar.get_style_context ();
            context.add_provider (
                headerbar_provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );

            if (application.debug) {
                this.add_css_class ("devel");
                this.set_title (_("Graphs (Development)"));
            }
        }

        [GtkCallback]
        private void perform_operation (Button button) {
            var action = this.application.lookup_action (
                "app.perform_operation"
            );
            action.activate (new Variant.string (button.get_buildable_id ()));
        }

        public void add_toast (Adw.Toast toast) {
            this.toast_overlay.add_toast (toast);
        }

        public void add_toast_string (string title) {
            this.add_toast (new Adw.Toast (title));
        }

        [GtkCallback]
        private void on_sidebar_toggle () {
            this.application.lookup_action ("toggle_sidebar").change_state (
                new Variant.boolean (this.split_view.get_collapsed ())
            );
        }
    }
}
