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
        super().__init__(application=application)
        self.set_transient_for(self.props.application.main_window)
        preferences = self.props.application.preferences
        self.transparent.set_active(preferences["export_figure_transparent"])
        self.items = \
            application.canvas.get_supported_filetypes_grouped().items()
        self.dpi.set_value(preferences["export_figure_dpi"])
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
        application = self.props.application
        dpi = int(self.dpi.get_value())
        fmt = utilities.get_selected_chooser_item(self.file_format)
        file_suffix = None
        for name, formats in self.items:
            if name == fmt:
                file_suffix = formats[0]
        filename = Path(application.canvas.get_default_filename()).stem
        transparent = self.transparent.get_active()

        def on_response(dialog, response):
            with contextlib.suppress(GLib.GError):
                destination = dialog.save_finish(response)
                file, stream = Gio.File.new_tmp("graphs-XXXXXX")
                stream.close()
                application.canvas.figure.savefig(
                    file.peek_path(), dpi=dpi, format=file_suffix,
                    transparent=transparent)
                file.move(destination, Gio.FileCopyFlags(1), None)
                application.main_window.add_toast(
                    _("Exported Figure"))

        dialog = Gtk.FileDialog()
        dialog.set_initial_name(f"{filename}.{file_suffix}")
        dialog.set_accept_label(_("Export"))
        dialog.set_filters(utilities.create_file_filters(
            [(fmt, [file_suffix])]))
        dialog.save(application.main_window, None, on_response)
        self.destroy()
