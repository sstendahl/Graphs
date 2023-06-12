# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, GLib, Gio, Gtk

from graphs import utilities


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/export_figure.ui")
class ExportFigureWindow(Adw.Window):
    __gtype_name__ = "ExportFigureWindow"
    file_format = Gtk.Template.Child()
    transparent = Gtk.Template.Child()
    dpi = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.set_transient_for(parent.main_window)
        self.transparent.set_active(
            self.parent.preferences.config["export_figure_transparent"])
        self.items = \
            self.parent.canvas.get_supported_filetypes_grouped().items()
        self.dpi.set_value(
            int(self.parent.preferences.config["export_figure_dpi"]))
        file_formats = []
        default_format = None
        for name, formats in self.items:
            file_formats.append(name)
            if self.parent.preferences.config["export_figure_filetype"] in \
                    formats:
                default_format = name
        utilities.populate_chooser(self.file_format, file_formats, False)
        if default_format is not None:
            utilities.set_chooser(self.file_format, default_format)
        self.present()

    @Gtk.Template.Callback()
    def on_accept(self, _button):
        dpi = int(self.dpi.get_value())
        fmt = utilities.get_selected_chooser_item(self.file_format)
        file_suffix = None
        for name, formats in self.items:
            if name == fmt:
                file_suffix = formats[0]
        filename = Path(self.parent.canvas.get_default_filename()).stem
        transparent = self.transparent.get_active()
        dialog = Gtk.FileDialog()
        dialog.set_initial_name(f"{filename}.{file_suffix}")
        dialog.set_accept_label(_("Export"))
        dialog.set_filters(utilities.create_file_filters([(fmt, file_suffix)]))
        dialog.save(
            self.parent.main_window, None, self.on_figure_save_response, dpi,
            file_suffix, transparent)
        self.destroy()

    def on_figure_save_response(
            self, dialog, response, dpi, file_suffix, transparent):
        with contextlib.suppress(GLib.GError):
            destination = dialog.save_finish(response)
            file, stream = Gio.File.new_tmp("graphs-XXXXXX")
            stream.close()
            self.parent.canvas.figure.savefig(
                file.peek_path(), dpi=dpi, format=file_suffix,
                transparent=transparent)
            file.move(destination, Gio.FileCopyFlags(1), None)
            self.parent.main_window.add_toast(_("Exported Figure"))
