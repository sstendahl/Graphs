// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/equation.ui")]
    public class EditItemEquationItemBox : Gtk.Box {
        [GtkChild]
        private unowned EditItemEquationGroup equation_group { get; }
        [GtkChild]
        private unowned Adw.ComboRow linestyle { get; }
        [GtkChild]
        private unowned Gtk.Scale linewidth { get; }

        public EditItemEquationItemBox (EquationItem item) {
            equation_group.setup (item);
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
        }
    }

}
