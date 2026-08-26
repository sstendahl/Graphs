// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/data.ui")]
    public class EditItemDataItemBox : Gtk.Box {
        [GtkChild]
        private unowned Adw.ComboRow linestyle { get; }
        [GtkChild]
        private unowned Gtk.Scale linewidth { get; }
        [GtkChild]
        private unowned Adw.ComboRow markerstyle { get; }
        [GtkChild]
        private unowned Gtk.Scale markersize { get; }
        [GtkChild]
        private unowned Adw.PreferencesGroup downsample_group { get; }
        [GtkChild]
        private unowned Adw.SwitchRow downsample { get; }

        public EditItemDataItemBox (DataItem item) {
            if (item.exceeds_downsample_threshold ()) {
                downsample_group.set_visible (true);
                item.bind_property (
                    "downsample",
                    downsample,
                    "active",
                    BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
                );
            }

            item.bind_property (
                "linestyle",
                linestyle,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "linewidth",
                linewidth.adjustment,
                "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "markerstyle",
                markerstyle,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "markersize",
                markersize.adjustment,
                "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
        }

        [GtkCallback]
        private void on_linestyle () {
            linewidth.set_sensitive (linestyle.get_selected () != 0);
        }

        [GtkCallback]
        private void on_markers () {
            markersize.set_sensitive (markerstyle.get_selected () != 0);
        }
    }
}
