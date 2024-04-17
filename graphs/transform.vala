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

        public TransformDialog (Application application) {
            this.transform_x.set_text ("X");
            this.transform_y.set_text ("Y");
            this.discard.set_visible (application.window.canvas.mode == 2);
            this.help_button.clicked.connect (() => {
                this.help_popover.popup ();
            });
            present (application.window);
        }

        [GtkCallback]
        private void on_accept () {
            this.accept.emit (
                this.transform_x.get_text (),
                this.transform_y.get_text (),
                this.discard.get_active ()
            );
            close ();
        }
    }
}
