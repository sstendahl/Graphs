// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * Item Box widget
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/item-box.ui")]
    public class ItemBox : Adw.ActionRow {

        [GtkChild]
        public unowned Gtk.CheckButton check_button { get; }

        [GtkChild]
        private unowned ColorButton color_button { get; }

        public Window window { get; construct set; }
        public Item item { get; construct set; }
        public uint index { get; construct set; }

        public ItemBox (Window window, Item item, uint index) {
            Object (
                window: window,
                item: item,
                index: index
            );
            color_button.color = item.get_rgba ();

            set_subtitle (item.typename);
            item.bind_property ("name", this, "title", 2);
            item.bind_property ("selected", check_button, "active", 2);
            item.notify["color"].connect (on_color_change);
            on_color_change ();
        }

        /**
         * Setup the actions for the ItemBox. This is omitted for rows created
         * for drag and drop.
         */
        public void setup_interactions (bool is_data_item) {
            var action_group = new SimpleActionGroup ();
            var delete_action = new SimpleAction ("delete", null);
            delete_action.activate.connect (() => {
                unowned string name = item.name;
                Item[] list = {item};
                window.data.delete_items (list);
                window.add_undo_toast (_("Deleted %s").printf (name));
            });
            action_group.add_action (delete_action);
            if (is_data_item) {
                var curve_fitting_action = new SimpleAction ("curve_fitting", null);
                curve_fitting_action.activate.connect (() => {
                    PythonHelper.create_curve_fitting_dialog (window, item);
                });
                action_group.add_action (curve_fitting_action);
            }
            if (index > 0) {
                var move_up_action = new SimpleAction ("move_up", null);
                move_up_action.activate.connect (() => {
                    change_position (index - 1);
                });
                action_group.add_action (move_up_action);
            }
            if (index + 1 < window.data.get_n_items ()) {
                var move_down_action = new SimpleAction ("move_down", null);
                move_down_action.activate.connect (() => {
                    change_position (index + 1);
                });
                action_group.add_action (move_down_action);
            }
            insert_action_group ("item_box", action_group);
        }

        private void on_color_change () {
            color_button.color = item.get_rgba ();
        }

        [GtkCallback]
        private void on_toggle () {
            bool new_value = check_button.get_active ();
            if (item.selected != new_value) {
                item.selected = new_value;
                window.data.add_history_state ();
            }
        }

        [GtkCallback]
        private void on_color () {
            item.set_rgba (color_button.color);
            window.data.add_history_state ();
        }

        public void change_position (uint source_index) {
            window.data.change_position (index, source_index);
            window.data.add_history_state ();
            window.data.add_view_history_state ();
        }
    }
}
