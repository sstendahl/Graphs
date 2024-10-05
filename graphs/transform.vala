// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Transform dialog
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/transform.ui")]
    public class TransformDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.EntryRow transform_x { get; }

        [GtkChild]
        private unowned Adw.EntryRow transform_y { get; }

        [GtkChild]
        private unowned Adw.SwitchRow discard { get; }

        [GtkChild]
        private unowned Button help_button { get; }

        [GtkChild]
        private unowned Popover help_popover { get; }

        public signal void accept (string x_input, string y_input, bool discard);

        public TransformDialog (Window window) {
            transform_x.set_text ("X");
            transform_y.set_text ("Y");
            discard.set_visible (window.canvas.mode == 2);
            help_button.clicked.connect (() => {
                help_popover.popup ();
            });
            present (window);
        }

        [GtkCallback]
        private void on_accept () {
            accept.emit (
                transform_x.get_text (),
                transform_y.get_text (),
                discard.get_active ()
            );
            close ();
        }
    }
}
