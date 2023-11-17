// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/smoothen_settings.ui")]
    public class SmoothenWindow : Adw.Window {
        [GtkChild]
        public unowned Adw.SpinRow savgol_window { get; }

        [GtkChild]
        public unowned Adw.SpinRow savgol_polynomial { get; }

        [GtkChild]
        public unowned Adw.SpinRow moving_average_box { get; }

        [GtkChild]
        public unowned Button reset_button { get; }

        public SmoothenWindow (Application application) {
            Object (
                application: application,
                transient_for: application.window
            );
            Tools.bind_settings_to_widgets (
                application.settings.get_child ("actions").get_child ("smoothen"), this
            );
            present ();
        }
    }
}
