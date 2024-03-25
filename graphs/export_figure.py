# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, GLib, GObject, Gio, Graphs, Gtk

from graphs import actions, file_io, ui, utilities


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/export_figure.ui")
class ExportFigureDialog(Adw.Dialog):
    __gtype_name__ = "GraphsExportFigureDialog"
    dpi = Gtk.Template.Child()
    file_format = Gtk.Template.Child()
    transparent = Gtk.Template.Child()

    file_formats = GObject.Property(type=object)
    application = GObject.Property(type=Graphs.Application)

    def __init__(self, application: Graphs.Application):
        self._canvas = application.get_window().get_canvas()
        valid_formats = self._canvas.get_supported_filetypes_grouped()
        valid_formats.pop("Tagged Image File Format")
        valid_formats.pop("Raw RGBA bitmap")
        valid_formats.pop("PGF code for LaTeX")
        super().__init__(
            application=application,
            file_formats=valid_formats,
        )
        self.file_format.set_model(
            Gtk.StringList.new(list(self.file_formats.keys())),
        )
        ui.bind_values_to_settings(
            application.get_settings_child("export-figure"),
            self,
        )
        self.on_file_format(None, None)
        self.file_format.connect("notify::selected", self.on_file_format)
        self.present(application.get_window())

    def on_file_format(self, _widget, _state) -> None:
        self.dpi.set_visible(
            self.file_format.get_selected() not in [0, 2, 4, 5],
        )

    @Gtk.Template.Callback()
    def on_accept(self, _button) -> None:
        file_format = self.file_format.get_selected_item().get_string()
        file_suffixes = self.props.file_formats[file_format]
        filename = \
            Path(self._canvas.get_default_filename()).stem

        def on_response(dialog, response):
            with contextlib.suppress(GLib.GError):
                file = dialog.save_finish(response)
                with file_io.open_wrapped(file, "wb") as wrapper:
                    self._canvas.figure.savefig(
                        wrapper,
                        format=file_suffixes[0],
                        dpi=int(self.dpi.get_value()),
                        transparent=self.transparent.get_active(),
                    )
                    action = Gio.SimpleAction.new(
                        "open-file-location",
                        None,
                    )
                    action.connect(
                        "activate",
                        actions.open_file_location,
                        file,
                    )
                    self.props.application.add_action(action)
                    toast = Adw.Toast.new(_("Exported Figure"))
                    toast.set_button_label(_("Open Location"))
                    toast.set_action_name("app.open-file-location")
                    self.props.application.get_window().add_toast(toast)
                    self.close()

        dialog = Gtk.FileDialog()
        dialog.set_initial_name(f"{filename}.{file_suffixes[0]}")
        dialog.set_accept_label(_("Export"))
        dialog.set_filters(
            utilities.create_file_filters([(file_format, file_suffixes)]),
        )
        dialog.save(self.props.application.get_window(), None, on_response)
