// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/errorbar-group.ui")]
    public class EditItemErrorBarGroup : Gtk.Box {
        [GtkChild]
        private unowned Adw.SwitchRow use_xerr { get; }
        [GtkChild]
        private unowned Adw.SwitchRow use_yerr { get; }
        [GtkChild]
        private unowned Adw.SwitchRow errbarsabove { get; }
        [GtkChild]
        private unowned ColorRow errcolor_row { get; }
        [GtkChild]
        private unowned Gtk.Scale errcapsize { get; }
        [GtkChild]
        private unowned Gtk.Scale errcapthick { get; }
        [GtkChild]
        private unowned Gtk.Scale errlinewidth { get; }

        public EditItemErrorBarGroup (DataItem item) {
            if (item.has_xerr ()) {
                use_xerr.set_visible (true);
                item.bind_property (
                    "showxerr",
                    use_xerr,
                    "active",
                    BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
                );
            }
            if (item.has_yerr ()) {
                use_yerr.set_visible (true);
                item.bind_property (
                    "showyerr",
                    use_yerr,
                    "active",
                    BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
                );
            }

            item.bind_property (
                "errbarsabove", errbarsabove, "active",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "errcapsize", errcapsize.adjustment, "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "errcapthick", errcapthick.adjustment, "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "errlinewidth", errlinewidth.adjustment, "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );

            errcolor_row.color = Tools.hex_to_rgba (item.errcolor);
            errcolor_row.color_chosen.connect (() => {
                item.errcolor = Tools.rgba_to_hex (errcolor_row.color);
            });
        }
    }
}
