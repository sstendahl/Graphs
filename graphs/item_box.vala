// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;
using Gdk;

namespace Graphs {
    /**
     * Item Box widget
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/item-box.ui")]
    public class ItemBox : Adw.ActionRow {

        [GtkChild]
        public unowned CheckButton check_button { get; }

        [GtkChild]
        private unowned Button color_button { get; }

        public Application application { get; construct set; }
        public Item item { get; construct set; }
        public uint index { get; construct set; }

        private CssProvider provider;

        public ItemBox (Application application, Item item, uint index) {
            Object (
                application: application,
                item: item,
                index: index
            );
            this.provider = new CssProvider ();
            color_button.get_style_context ().add_provider (
                provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );

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
        public void setup_interactions () {
            this.activated.connect (() => {
                application.python_helper.create_edit_item_dialog (item);
            });

            var action_group = new SimpleActionGroup ();
            var delete_action = new SimpleAction ("delete", null);
            delete_action.activate.connect (() => {
                string name = item.name;
                Item[] list = {item};
                application.data.delete_items (list);
                application.window.add_undo_toast (_("Deleted %s").printf (name));
            });
            action_group.add_action (delete_action);
            var curve_fitting_action = new SimpleAction ("curve_fitting", null);
            curve_fitting_action.activate.connect (() => {
                application.python_helper.create_curve_fitting_dialog (item);
            });
            action_group.add_action (curve_fitting_action);
            if (index > 0) {
                var move_up_action = new SimpleAction ("move_up", null);
                move_up_action.activate.connect (() => {
                    change_position (index - 1);
                });
                action_group.add_action (move_up_action);
            }
            if (index + 1 < application.data.get_n_items ()) {
                var move_down_action = new SimpleAction ("move_down", null);
                move_down_action.activate.connect (() => {
                    change_position (index + 1);
                });
                action_group.add_action (move_down_action);
            }
            insert_action_group ("item_box", action_group);
        }

        private void on_color_change () {
            string c = item.color;
            string o = item.alpha.to_string ();
            provider.load_from_string (@"button { color: $c; opacity: $o; }");
        }

        [GtkCallback]
        private void on_toggle () {
            bool new_value = check_button.get_active ();
            if (item.selected != new_value) {
                item.selected = new_value;
                application.data.add_history_state ();
            }
        }

        [GtkCallback]
        private void choose_color () {
            var dialog = new ColorDialog ();
            dialog.choose_rgba.begin (
                application.window,
                item.get_rgba (),
                null,
                (d, result) => {
                    try {
                        item.set_rgba (dialog.choose_rgba.end (result));
                        application.data.add_history_state ();
                    } catch {}
                }
            );
        }

        public void change_position (uint source_index) {
            application.data.change_position (index, source_index);
            application.data.add_history_state ();
            application.data.add_view_history_state ();
        }
    }
}
