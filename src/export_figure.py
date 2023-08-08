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

    def __init__(self, application):
        super().__init__(application=application,
                         transient_for=application.main_window)
        preferences = self.props.application.preferences

        # Set values in Export Figure dialog:
        self.transparent.set_active(preferences["export_figure_transparent"])
        self.items = \
            application.canvas.get_supported_filetypes_grouped().items()
        self.dpi.set_value(int(preferences["export_figure_dpi"]))
        file_formats = []
        default_format = None
        for name, formats in self.items:
            file_formats.append(name)
            if preferences["export_figure_filetype"] in formats:
                default_format = name
        utilities.populate_chooser(self.file_format, file_formats, False)
        if default_format is not None:
            utilities.set_chooser(self.file_format, default_format)
        self.present()

    @Gtk.Template.Callback()
    def on_accept(self, _button):
        dpi = int(self.dpi.get_value())
        fmt = utilities.get_selected_chooser_item(self.file_format)
        file_suffixes = None
        for name, formats in self.items:
            if name == fmt:
                file_suffixes = formats
        filename = \
            Path(self.props.application.canvas.get_default_filename()).stem
        transparent = self.transparent.get_active()

        self.props.application.preferences.update({
            "export_figure_filetype": file_suffixes[0],
            "export_figure_transparent": transparent,
            "export_figure_dpi": dpi,
        })

        def on_response(dialog, response):
            with contextlib.suppress(GLib.GError):
                destination = dialog.save_finish(response)
                file, stream = Gio.File.new_tmp("graphs-XXXXXX")
                stream.close()
                self.props.application.canvas.figure.savefig(
                    file.peek_path(), dpi=dpi, format=file_suffixes[0],
                    transparent=transparent)
                file.move(destination, Gio.FileCopyFlags(1), None)
                self.props.application.main_window.add_toast(
                    _("Exported Figure"))

        dialog = Gtk.FileDialog()
        dialog.set_initial_name(f"{filename}.{file_suffixes[0]}")
        dialog.set_accept_label(_("Export"))
        dialog.set_filters(utilities.create_file_filters(
            [(fmt, file_suffixes)]))
        dialog.save(self.props.application.main_window, None, on_response)
        self.destroy()
