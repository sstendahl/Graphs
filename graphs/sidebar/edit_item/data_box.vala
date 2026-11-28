// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/data.ui")]
    private class EditItemDataItemBox : Gtk.Box {
        [GtkChild]
        private unowned Adw.ComboRow plottype { get; }
        [GtkChild]
        private unowned Adw.ComboRow stepposition { get; }
        [GtkChild]
        private unowned Adw.ActionRow barwidth_row { get; }
        [GtkChild]
        private unowned Gtk.Scale barwidth { get; }
        [GtkChild]
        private unowned Adw.ComboRow baralign { get; }
        [GtkChild]
        private unowned Adw.ActionRow edgewidth_row { get; }
        [GtkChild]
        private unowned Gtk.Scale edgewidth { get; }
        [GtkChild]
        private unowned ColorRow edgecolor_row { get; }
        [GtkChild]
        private unowned Adw.ComboRow linestyle { get; }
        [GtkChild]
        private unowned Adw.ActionRow linewidth_row { get; }
        [GtkChild]
        private unowned Gtk.Scale linewidth { get; }
        [GtkChild]
        private unowned Adw.ComboRow markerstyle { get; }
        [GtkChild]
        private unowned Adw.ActionRow markersize_row { get; }
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
                "plottype",
                plottype,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "stepposition",
                stepposition,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "barwidth",
                barwidth.adjustment,
                "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "baralign",
                baralign,
                "selected",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
            item.bind_property (
                "edgewidth",
                edgewidth.adjustment,
                "value",
                BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL
            );
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

            edgecolor_row.color = Tools.hex_to_rgba (item.edgecolor);
            edgecolor_row.color_chosen.connect (() => {
                item.edgecolor = Tools.rgba_to_hex (edgecolor_row.color);
            });
        }

        [GtkCallback]
        private void on_plottype () {
            var type = (DataPlotType) plottype.get_selected ();
            bool bars = type == BARS;
            stepposition.set_visible (type == STAIRS);
            barwidth_row.set_visible (bars);
            baralign.set_visible (bars);
            edgewidth_row.set_visible (bars);
            edgecolor_row.set_visible (bars);
            linestyle.set_visible (!bars);
            linewidth_row.set_visible (!bars);
            markerstyle.set_visible (!bars);
            markersize_row.set_visible (!bars);
        }

        [GtkCallback]
        private void on_edgewidth () {
            edgecolor_row.set_sensitive (edgewidth.get_value () != 0);
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
