// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/operations.ui")]
    public class Operations : Box {

        [GtkChild]
        private unowned Adw.Bin stack_switcher_bin { get; }

        [GtkChild]
        private unowned Stack stack { get; }

        [GtkChild]
        public unowned Button shift_button { get; }

        [GtkChild]
        public unowned Adw.SplitButton smoothen_button { get; }

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

        private Window _window;

        construct {
            InlineStackSwitcher stack_switcher = new InlineStackSwitcher ();
            stack_switcher.stack = stack;
            stack_switcher.add_css_class ("compact");
            stack_switcher.set_hexpand (true);
            stack_switcher_bin.set_child (stack_switcher);
        }

        public Operations (Window window) {
            this._window = window;

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
                _window.data.notify["items-selected"].connect (() => {
                    validate_entry (entry, button);
                });
                validate_entry (entry, button);
            }
        }

        [GtkCallback]
        private void perform_operation (Button button) {
            var action = _window.lookup_action (
                "perform_operation"
            );
            string name = button.get_buildable_id ()[0:-7];
            action.activate (new Variant.string (name));
        }

        private void validate_entry (Entry entry, Button button) {
            var application = _window.application as Application;
            double? val = application.python_helper.evaluate_string (entry.get_text ());
            if (val == null) {
                entry.add_css_class ("error");
                button.set_sensitive (false);
            } else {
                entry.remove_css_class ("error");
                button.set_sensitive (_window.data.items_selected);
            }
        }
    }
}
