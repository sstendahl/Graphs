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
        private unowned Adw.SpinRow savgol_window { get; }

        [GtkChild]
        private unowned Adw.SpinRow savgol_polynomial { get; }

        [GtkChild]
        private unowned Adw.SpinRow moving_average_box { get; }

        private GLib.Settings settings { get; set; }

        public SmoothenDialog (Window window) {
            Object ();
            this.settings = Application.get_settings_child ("actions/smoothen");

            settings.bind ("savgol-window", savgol_window, "value", 0);
            settings.bind ("savgol-polynomial", savgol_polynomial, "value", 0);
            settings.bind ("moving-average-box", moving_average_box, "value", 0);

            present (window);
        }

        [GtkCallback]
        private void on_reset () {
            Tools.reset_settings (settings);
        }
    }
}
