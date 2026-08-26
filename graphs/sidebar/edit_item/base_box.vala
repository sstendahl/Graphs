// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/base.ui")]
    public class EditItemBaseBox : Gtk.Box {
        [GtkChild]
        private unowned Adw.EntryRow name_entry { get; }
        [GtkChild]
        private unowned Adw.ComboRow xposition { get; }
        [GtkChild]
        private unowned Adw.ComboRow yposition { get; }
        [GtkChild]
        private unowned Adw.SwitchRow legend { get; }

        public EditItemBaseBox (Item item) {
            item.bind_property (
                "name",
                name_entry,
                "text",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "xposition",
                xposition,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "yposition",
                yposition,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            if (item is LegendableItem) {
                item.bind_property (
                    "legend",
                    legend,
                    "active",
                    BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
                );
                legend.visible = true;
            }
        }
    }
}
