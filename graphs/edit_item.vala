// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/edit-item-data.ui")]
    public class EditItemDataItemBox : Box {

        [GtkChild]
        public unowned Adw.ComboRow linestyle { get; }

        [GtkChild]
        public unowned Scale linewidth { get; }

        [GtkChild]
        public unowned Adw.ComboRow markerstyle { get; }

        [GtkChild]
        public unowned Scale markersize { get; }

        [GtkCallback]
        private void on_linestyle () {
            linewidth.set_sensitive (linestyle.get_selected () != 0);
        }

        [GtkCallback]
        private void on_markers () {
            markersize.set_sensitive (markerstyle.get_selected () != 0);
        }
    }

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/edit-item-equation.ui")]
    public class EditItemEquationItemBox : Box {

        [GtkChild]
        public unowned Adw.EntryRow equation { get; }

        [GtkChild]
        public unowned Adw.ButtonRow simplify { get; }

        [GtkChild]
        public unowned Adw.ComboRow linestyle { get; }

        [GtkChild]
        public unowned Scale linewidth { get; }

        [GtkCallback]
        private void on_linestyle () {
            linewidth.set_sensitive (linestyle.get_selected () != 0);
        }
    }
}
