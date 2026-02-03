// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Generate Data dialog.
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/generate-data.ui")]
    public class GenerateDataDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.EntryRow equation { get; }

        [GtkChild]
        private unowned Adw.EntryRow xstart { get; }

        [GtkChild]
        private unowned Adw.EntryRow xstop { get; }

        [GtkChild]
        private unowned Adw.SpinRow steps { get; }

        [GtkChild]
        private unowned Adw.ComboRow scale { get; }

        [GtkChild]
        private unowned Button confirm_button { get; }

        [GtkChild]
        private unowned Adw.EntryRow item_name { get; }

        private Window window;
        private Application application;
        private GLib.Settings settings;

        public GenerateDataDialog (Window window) {
            Object ();
            this.window = window;
            this.application = window.application as Application;
            this.settings = application.get_settings_child ("generate-data");
            this.equation.set_text (settings.get_string ("equation"));
            this.xstart.set_text (settings.get_string ("xstart"));
            this.xstop.set_text (settings.get_string ("xstop"));
            this.steps.set_value (settings.get_int ("steps"));
            this.scale.set_selected (settings.get_int ("scale"));
            present (window);
        }

        private void set_confirm_sensitivity () {
            bool invalid = false;
            Widget[] widgets = {equation, xstart, xstop};
            foreach (Widget widget in widgets) {
                invalid = invalid || widget.has_css_class ("error");
            }
            confirm_button.set_sensitive (!invalid);
        }

        [GtkCallback]
        private void on_accept () {
            this.settings.set_string ("equation", this.equation.get_text ());
            this.settings.set_string ("xstart", xstart.get_text ());
            this.settings.set_string ("xstop", xstop.get_text ());
            this.settings.set_int ("steps", (int) this.steps.get_value ());
            this.settings.set_int ("scale", (int) this.scale.get_selected ());
            Item item = application.python_helper.generate_data (window, item_name.get_text ());
            Item[] items = {item};
            window.data.add_items (items);
            window.data.optimize_limits ();
            close ();
        }

        [GtkCallback]
        private void on_equation_change () {
            if (application.python_helper.validate_equation (equation.get_text ())) {
                equation.remove_css_class ("error");
            } else {
                equation.add_css_class ("error");
            }
            set_confirm_sensitivity ();
        }

        [GtkCallback]
        private void on_entry_change (Object object, ParamSpec _param_spec) {
            var entry = object as Adw.EntryRow;
            if (try_evaluate_string (entry.get_text ())) {
                entry.remove_css_class ("error");
            } else {
                entry.add_css_class ("error");
            }
            set_confirm_sensitivity ();
        }
    }
}
