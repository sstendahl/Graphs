// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Add Equation dialog.
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/add-equation.ui")]
    public class AddEquationDialog : Adw.Dialog {

        [GtkChild]
        public unowned Adw.EntryRow equation { get; }

        [GtkChild]
        public unowned Adw.EntryRow x_start { get; }

        [GtkChild]
        public unowned Adw.EntryRow x_stop { get; }

        [GtkChild]
        public unowned Button confirm_button { get; }

        [GtkChild]
        public unowned Adw.EntryRow item_name { get; }

        [GtkChild]
        private unowned Adw.ToastOverlay toast_overlay { get; }

        private Application application;

        public AddEquationDialog (Application application) {
            Object ();
            this.application = application;
            Tools.bind_settings_to_widgets (
                application.get_settings_child ("add-equation"), this
            );
            present (application.window);
        }

        [GtkCallback]
        private void on_accept () {
            string error = application.python_helper.add_equation (item_name.get_text ());
            if (error == "") close ();
            else toast_overlay.add_toast (new Adw.Toast (error));
        }

        [GtkCallback]
        private void on_entry_change (Object object, ParamSpec? spec) {
            var entry = object as Adw.EntryRow;
            double? val = application.python_helper.evaluate_string (entry.get_text ());
            if (val == null) {
                entry.add_css_class ("error");
                confirm_button.set_sensitive(false);
            } else {
                entry.remove_css_class ("error");
                confirm_button.set_sensitive(true);
            }
        }

        [GtkCallback]
        private void on_equation_change (Object object, ParamSpec? spec) {
            var entry = object as Adw.EntryRow;
            double? val = application.python_helper.validate_equation (entry.get_text ());
            if (val == null) {
                entry.add_css_class ("error");
                confirm_button.set_sensitive(false);
            } else {
                entry.remove_css_class ("error");
                confirm_button.set_sensitive(true);
            }
        }
    }
}
