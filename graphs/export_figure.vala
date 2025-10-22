// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Export figure dialog
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/export-figure.ui")]
    public class ExportFigureDialog : Adw.Dialog {

        [GtkChild]
        public unowned Adw.SwitchRow transparent { get; }

        [GtkChild]
        public unowned Adw.ComboRow file_format { get; }

        [GtkChild]
        public unowned Adw.SwitchRow use_window_size { get; }

        [GtkChild]
        public unowned Adw.SpinRow width { get; }

        [GtkChild]
        public unowned Adw.SpinRow height { get; }

        private Window window;
        private Application application;

        public ExportFigureDialog (Window window) {
            Object ();
            this.window = window;
            this.application = window.application as Application;

            Tools.bind_settings_to_widgets (
                application.get_settings_child ("export-figure"), this
            );

            if (use_window_size.get_active ()) {
                int canvas_width = window.canvas.get_width ();
                int canvas_height = window.canvas.get_height ();
                width.set_value (canvas_width);
                height.set_value (canvas_height);
            }

            on_use_window_size_changed ();
            present (window);
        }

        [GtkCallback]
        private void on_use_window_size_changed () {
            bool use_window = use_window_size.get_active ();
            width.set_sensitive (!use_window);
            height.set_sensitive (!use_window);

            if (use_window) {
                int canvas_width = window.canvas.get_width ();
                int canvas_height = window.canvas.get_height ();
                width.set_value (canvas_width);
                height.set_value (canvas_height);
            }
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
            var selected = file_format.get_selected_item () as StringObject;
            filter.name = selected.get_string ();
            filter.add_suffix (suffix);
            filter_store.append (filter);
            dialog.set_filters (filter_store);
            dialog.save.begin (window, null, (d, r) => {
                try {
                    File file = dialog.save.end (r);

                    int export_width = (int) width.get_value ();
                    int export_height = (int) height.get_value ();

                    window.canvas.save (
                        file, suffix,
                        settings.get_boolean ("transparent"),
                        export_width, export_height
                    );
                    window.add_toast_string_with_file (
                        _("Exported Figure"), file
                    );
                    close ();
                } catch {}
            });
        }
    }
}
