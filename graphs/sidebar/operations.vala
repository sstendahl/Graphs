// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/operations.ui")]
    public class Operations : Box {

        [GtkChild]
        public unowned Button shift_button { get; }

        [GtkChild]
        public unowned Adw.SplitButton smoothen_button { get; }

        [GtkChild]
        private unowned Button cut_button { get; }

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
        private bool entries_sensitive = false;
        private bool cut_sensitive = false;

        public Operations (Window window) {
            this._window = window;

            window.notify["mode"].connect (on_mode_change);

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

        public void set_entry_sensitivity (bool entries_sensitive) {
            this.entries_sensitive = entries_sensitive;
            validate_entry (translate_x_entry, translate_x_button);
            validate_entry (translate_y_entry, translate_y_button);
            validate_entry (multiply_x_entry, multiply_x_button);
            validate_entry (multiply_y_entry, multiply_y_button);
        }

        public void set_cut_sensitivity (bool sensitive) {
            this.cut_sensitive = sensitive;
            on_mode_change ();
        }

        private void on_mode_change () {
            cut_button.set_sensitive (cut_sensitive && _window.mode == 2);
        }

        private void validate_entry (Entry entry, Button button) {
            if (PythonHelper.evaluate_string (entry.get_text ())) {
                entry.remove_css_class ("error");
                button.set_sensitive (entries_sensitive);
            } else {
                entry.add_css_class ("error");
                button.set_sensitive (false);
            }
        }
    }
}
