// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;
using Gdk;

namespace Graphs {
    /**
     * Item Box widget
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/item-box.ui")]
    public class ItemBox : Box {

        [GtkChild]
        private unowned Label label { get; }

        [GtkChild]
        public unowned CheckButton check_button { get; }

        [GtkChild]
        private unowned Button color_button { get; }

        public Application application { get; construct set; }
        public Item item { get; construct set; }
        public int index { get; construct set; }
        public GestureClick click_gesture { get; private set; }
        public DragSource drag_source { get; private set; }
        public DropTarget drop_target { get; private set; }

        private CssProvider provider;

        public ItemBox (Application application, Item item, int index) {
            Object (
                application: application,
                item: item,
                index: index
            );
            this.provider = new CssProvider ();
            this.color_button.get_style_context ().add_provider (
                this.provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );

            this.item.bind_property ("name", this.label, "label", 2);
            this.item.bind_property ("selected", this.check_button, "active", 2);
            this.item.notify["color"].connect (on_color_change);
            on_color_change ();

            this.click_gesture = new GestureClick ();
            this.click_gesture.released.connect (() => {
                this.application.python_helper.create_edit_item_dialog (this.item);
            });

            this.drag_source = new DragSource ();
            this.drag_source.set_actions (DragAction.COPY);
            this.drag_source.prepare.connect ((s, x, y) => {
                Widget widget = this.get_parent ();
                widget.add_css_class ("card");
                var paintable = new WidgetPaintable (widget);
                this.drag_source.set_icon (paintable, (int) x, (int) y);
                return new ContentProvider.for_value (this.index);
            });
            this.drop_target = new DropTarget (typeof (int), DragAction.COPY);
            this.drop_target.drop.connect ((t, val, x, y) => {
                this.change_position (val.get_int ());
                return true;
            });

            var action_group = new SimpleActionGroup ();
            var delete_action = new SimpleAction ("delete", null);
            delete_action.activate.connect (() => {
                string name = this.item.name;
                Item[] list = {this.item};
                this.application.data.delete_items (list);
                var toast = new Adw.Toast (_("Deleted %s").printf (name));
                toast.set_button_label (_("Undo"));
                toast.set_action_name ("app.undo");
                this.application.window.add_toast (toast);
            });
            action_group.add_action (delete_action);
            var curve_fitting_action = new SimpleAction ("curve_fitting", null);
            curve_fitting_action.activate.connect (() => {
                this.application.python_helper.create_curve_fitting_dialog (this.item);
            });
            action_group.add_action (curve_fitting_action);
            if (this.index > 0) {
                var move_up_action = new SimpleAction ("move_up", null);
                move_up_action.activate.connect (() => {
                    this.change_position (this.index - 1);
                });
                action_group.add_action (move_up_action);
            }
            if (this.index + 1 < this.application.data.get_n_items ()) {
                var move_down_action = new SimpleAction ("move_down", null);
                move_down_action.activate.connect (() => {
                    this.change_position (this.index + 1);
                });
                action_group.add_action (move_down_action);
            }
            this.insert_action_group ("item_box", action_group);
        }

        private void on_color_change () {
            string c = this.item.color;
            string o = this.item.alpha.to_string ();
            this.provider.load_from_string (@"button { color: $c; opacity: $o; }");
        }

        [GtkCallback]
        private void on_toggle () {
            bool new_value = this.check_button.get_active ();
            if (this.item.selected != new_value) {
                this.item.selected = new_value;
                this.application.data.add_history_state ();
            }
        }

        [GtkCallback]
        private void choose_color () {
            var dialog = new ColorDialog ();
            dialog.choose_rgba.begin (
                this.application.window,
                this.item.get_rgba (),
                null,
                (d, result) => {
                    try {
                        this.item.set_rgba (dialog.choose_rgba.end (result));
                        this.application.data.add_history_state ();
                    } catch {}
                }
            );
        }

        private void change_position (int source_index) {
            Data data = this.application.data;
            data.change_position (this.index, source_index);
            data.add_history_state ();
            data.add_view_history_state ();
        }
    }
}
