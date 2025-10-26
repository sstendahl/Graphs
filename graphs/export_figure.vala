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
        private unowned Adw.SwitchRow transparent { get; }

        [GtkChild]
        private unowned Adw.ComboRow file_format { get; }

        [GtkChild]
        private unowned Adw.SwitchRow use_window_size { get; }

        [GtkChild]
        private unowned Adw.SpinRow width { get; }

        [GtkChild]
        private unowned Adw.SpinRow height { get; }

        private Window window;
        private GLib.Settings settings;

        public ExportFigureDialog (Window window) {
            Object ();
            this.window = window;
            var application = window.application as Application;
            this.settings = application.get_settings_child ("export-figure");

            Tools.bind_comborow_settings (settings, "file-format", file_format);
            settings.bind ("transparent", transparent, "active", 0);
            settings.bind ("use-window-size", use_window_size, "active", 0);
            settings.bind ("width", width, "value", 0);
            settings.bind ("height", height, "value", 0);

            on_use_window_size_changed ();
            present (window);
        }

        [GtkCallback]
        private void on_use_window_size_changed () {
            bool use_window = use_window_size.get_active ();
            width.set_sensitive (!use_window);
            height.set_sensitive (!use_window);

            if (use_window) {
                width.set_value (window.canvas.get_width ());
                height.set_value (window.canvas.get_height ());
            }
        }

        [GtkCallback]
        private void on_accept () {
            string filename = C_("filename", "Exported Figure");
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
