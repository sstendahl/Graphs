// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Smoothen settings dialog
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/smoothen-settings.ui")]
    public class SmoothenDialog : Adw.Dialog {
        [GtkChild]
        public unowned Adw.SpinRow savgol_window { get; }

        [GtkChild]
        public unowned Adw.SpinRow savgol_polynomial { get; }

        [GtkChild]
        public unowned Adw.SpinRow moving_average_box { get; }

        private Application application { get; set; }

        public SmoothenDialog (Application application) {
            Object ();
            this.application = application;
            Tools.bind_settings_to_widgets (
                application.get_settings_child ("actions/smoothen"), this
            );
            present (application.window);
        }

        [GtkCallback]
        private void on_reset () {
            Tools.reset_settings (application.get_settings_child ("actions/smoothen"));
        }
    }
}
