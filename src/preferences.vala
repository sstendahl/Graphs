// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/preferences.ui")]
    public class PreferencesWindow : Adw.PreferencesWindow {

        [GtkChild]
        public unowned Adw.ComboRow center { get; }

        [GtkChild]
        public unowned Adw.ComboRow handle_duplicates { get; }

        [GtkChild]
        public unowned Adw.SwitchRow hide_unselected { get; }

        [GtkChild]
        public unowned Adw.SwitchRow override_item_properties { get; }

        public PreferencesWindow (Application application) {
            Object (
                application: application,
                transient_for: application.window
            );
            Tools.bind_settings_to_widgets (
                application.settings.get_child("general"), this
            );
            present ();
        }
    }
}
