# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, GLib, GObject, Gtk

from graphs import file_io, ui, utilities


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/export_figure.ui")
class ExportFigureWindow(Adw.Window):
    __gtype_name__ = "GraphsExportFigureWindow"
    dpi = Gtk.Template.Child()
    file_format = Gtk.Template.Child()
    transparent = Gtk.Template.Child()

    file_formats = GObject.Property(type=object)

    def __init__(self, application):
        self._canvas = application.get_window().get_canvas()
        super().__init__(
            application=application, transient_for=application.get_window(),
            file_formats=self._canvas.get_supported_filetypes_grouped(),
        )
        self.file_format.set_model(
            Gtk.StringList.new(list(self.file_formats.keys())))
        ui.bind_values_to_settings(
            self.get_application().get_settings_child("export-figure"), self)
        self.dpi.set_visible(self.file_format.get_selected()
                             not in [0, 2, 3, 7])
        self.file_format.connect("notify::selected", self.on_file_format)
        self.present()

    def on_file_format(self, _widget, _state):
        self.dpi.set_visible(self.file_format.get_selected()
                             not in [0, 2, 3, 7])

    @Gtk.Template.Callback()
    def on_accept(self, _button):
        file_format = self.file_format.get_selected_item().get_string()
        file_suffixes = self.props.file_formats[file_format]
        filename = \
            Path(self._canvas.get_default_filename()).stem

        def on_response(dialog, response):
            with contextlib.suppress(GLib.GError):
                file = dialog.save_finish(response)
                with file_io.open_wrapped(file, "wb") as wrapper:
                    self._canvas.figure.savefig(
                        wrapper, format=file_suffixes[0],
                        dpi=int(self.dpi.get_value()),
                        transparent=self.transparent.get_active(),
                    )
                    self.get_application().get_window().add_toast_string(
                        _("Exported Figure"))
                    self.destroy()

        dialog = Gtk.FileDialog()
        dialog.set_initial_name(f"{filename}.{file_suffixes[0]}")
        dialog.set_accept_label(_("Export"))
        dialog.set_filters(utilities.create_file_filters(
            [(file_format, file_suffixes)]))
        dialog.save(self.get_application().get_window(), None, on_response)
