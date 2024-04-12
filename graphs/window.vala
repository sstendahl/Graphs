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
        private unowned MenuButton view_menu_button { get; }

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

        public Canvas canvas {
            get { return (Canvas) this.toast_overlay.get_child (); }
            set {
                value.bind_property ("mode", this, "mode", 2);
                this.toast_overlay.set_child (value);
            }
        }

        public CssProvider headerbar_provider { get; private set; }

        public Window (Application application) {
            Object (application: application);
            Data data = application.data;
            data.bind_property (
                "items_selected", this.shift_button, "sensitive", 2
            );
            data.bind_property ("empty", this.item_list, "visible", 4);

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
            string name = button.get_buildable_id ()[0:-7];
            action.activate (new Variant.string (name));
        }

        public void add_toast (Adw.Toast toast) {
            this.toast_overlay.add_toast (toast);
        }

        public void add_toast_string (string title) {
            this.add_toast (new Adw.Toast (title));
        }

        public void add_toast_string_with_file (string title, File file) {
            SimpleAction action = new SimpleAction ("open-file-location", null);
            action.activate.connect (() => {
                Tools.open_file_location (file);
            });
            this.application.add_action (action);
            var toast = new Adw.Toast (title);
            toast.set_button_label (_("Open Location"));
            toast.set_action_name ("app.open-file-location");
            this.add_toast (toast);
        }

        [GtkCallback]
        private void on_sidebar_toggle () {
            this.application.lookup_action ("toggle_sidebar").change_state (
                new Variant.boolean (this.split_view.get_collapsed ())
            );
        }

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
