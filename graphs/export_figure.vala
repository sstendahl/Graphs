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
        private unowned Adw.SpinRow width { get; }

        [GtkChild]
        private unowned Adw.SpinRow height { get; }

        private Window window;
        private GLib.Settings settings;

        public ExportFigureDialog (Window window) {
            Object ();
            this.window = window;
            this.settings = Application.get_settings_child ("export-figure");

            file_format.set_selected (settings.get_enum ("file-format"));
            transparent.set_active (settings.get_boolean ("transparent"));
            width.set_value (settings.get_int ("width"));
            height.set_value (settings.get_int ("height"));

            present (window);
        }

        [GtkCallback]
        private void on_use_window_size () {
            width.set_value (window.canvas.get_width ());
            height.set_value (window.canvas.get_height ());
        }

        [GtkCallback]
        private void on_accept () {
            string filename = C_("filename", "Exported Figure");
            string old_suffix = settings.get_string ("file-format");
            settings.set_enum ("file-format", (int) file_format.get_selected ());
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

                    settings.set_string ("file-format", suffix);
                    settings.set_boolean ("transparent", transparent.get_active ());
                    settings.set_int ("width", (int) width.get_value ());
                    settings.set_int ("height", (int) height.get_value ());

                    PythonHelper.export_figure (file, settings, window.data);
                    window.add_toast_string_with_file (
                        _("Exported Figure"), file
                    );

                    close ();
                } catch {
                    settings.set_string ("file-format", old_suffix);
                }
            });
        }
    }
}
