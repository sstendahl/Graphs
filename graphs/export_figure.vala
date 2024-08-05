// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    private const uint[] FORMATS_WITH_DPI = {1, 3, 6};

    /**
     * Export figure dialog
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/export-figure.ui")]
    public class ExportFigureDialog : Adw.Dialog {

        [GtkChild]
        public unowned Adw.SpinRow dpi { get; }

        [GtkChild]
        public unowned Adw.SwitchRow transparent { get; }

        [GtkChild]
        public unowned Adw.ComboRow file_format { get; }

        private Application application;

        public ExportFigureDialog (Application application) {
            Object ();
            this.application = application;
            Tools.bind_settings_to_widgets (
                application.get_settings_child ("export-figure"), this
            );
            present (application.window);
        }

        [GtkCallback]
        private void on_file_format () {
            this.dpi.set_visible (
                this.file_format.get_selected () in FORMATS_WITH_DPI
            );
        }

        [GtkCallback]
        private void on_accept () {
            string filename = C_("filename", "Exported Figure");
            GLib.Settings settings = application.get_settings_child ("export-figure");
            string suffix = settings.get_string ("file-format");

            var dialog = new FileDialog ();
            dialog.set_initial_name (@"$filename.$suffix");
            dialog.set_accept_label (_("Export"));
            GLib.ListStore filter_store = new GLib.ListStore (typeof (FileFilter));
            var filter = new FileFilter ();
            StringObject selected = (StringObject) this.file_format.get_selected_item ();
            filter.name = selected.get_string ();
            filter.add_suffix (suffix);
            filter_store.append (filter);
            dialog.set_filters (filter_store);
            dialog.save.begin (this.application.window, null, (d, r) => {
                try {
                    File file = dialog.save.end (r);
                    application.window.canvas.save (
                        file, suffix, settings.get_int ("dpi"),
                        settings.get_boolean ("transparent")
                    );
                    close ();
                } catch {}
            });
        }
    }
}
