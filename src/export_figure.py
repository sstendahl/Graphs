# SPDX-License-Identifier: GPL-3.0-or-later
import pathlib

from gi.repository import Adw, Gtk, GLib

from graphs import utilities


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/export_figure.ui")
class ExportFigureWindow(Adw.Window):
    __gtype_name__ = "ExportFigureWindow"
    confirm_button = Gtk.Template.Child()
    file_format = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.set_transient_for(parent.main_window)
        self.confirm_button.connect("clicked", self.accept)
        items = self.parent.canvas.get_supported_filetypes_grouped().items()
        file_formats = []
        default_format = None
        for name, formats in items:
            file_formats.append(name)
            if self.parent.canvas.get_default_filetype() in formats:
                default_format = name
        utilities.populate_chooser(self.file_format, file_formats)
        if default_format is not None:
            utilities.set_chooser(self.file_format, default_format)
        self.present()

    def accept(self, _):
        fmt = self.file_format.get_selected_item().get_string()
        file_suffix = None
        items = self.parent.canvas.get_supported_filetypes_grouped().items()
        for name, formats in items:
            if name == fmt:
                file_suffix = formats[0]
        filename = pathlib.Path(self.parent.canvas.get_default_filename()).stem
        dialog = Gtk.FileDialog()
        dialog.set_initial_name(f"{filename}.{file_suffix}")
        dialog.set_accept_label("Export")
        dialog.save(
            self.parent.main_window, None, self.on_figure_save_response,
            file_suffix)
        self.destroy()

    def on_figure_save_response(self, dialog, response, file_suffix):
        try:
            path = dialog.save_finish(response).get_path()
            if path is not None:
                self.parent.canvas.figure.savefig(path, format=file_suffix)
        except GLib.GError:
            pass
