# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for exporting the figure."""
import contextlib
from gettext import gettext as _, pgettext as C_

from gi.repository import Adw, GLib, GObject, Gio, Graphs, Gtk

from graphs import actions, file_io, ui, utilities

_FILE_SUFFIXES = (
    ("eps", ),  # Encapsulated Postscript
    ("jpeg", "jpg"),  # Joint Photographic Experts Group
    ("pdf", ),  # Portable Document Format
    ("png", ),  # Portable Network Graphics
    ("ps", ),  # Postscript
    ("svg", "svgz"),  # Scalable Vector Graphics
    ("webp", ),  # WebP Image Format
)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/export_figure.ui")
class ExportFigureDialog(Adw.Dialog):
    """Dialog for exporting the figure."""

    __gtype_name__ = "GraphsExportFigureDialog"
    dpi = Gtk.Template.Child()
    file_format = Gtk.Template.Child()
    transparent = Gtk.Template.Child()

    application = GObject.Property(type=Graphs.Application)

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)
        ui.bind_values_to_settings(
            application.get_settings_child("export-figure"),
            self,
        )
        self.on_file_format(None, None)
        self.file_format.connect("notify::selected", self.on_file_format)
        self.present(application.get_window())

    def on_file_format(self, _widget, _state) -> None:
        """Handle file format change."""
        self.dpi.set_visible(
            self.file_format.get_selected() not in [0, 2, 4, 5],
        )

    @Gtk.Template.Callback()
    def on_accept(self, _button) -> None:
        """Export the figure."""
        file_suffixes = _FILE_SUFFIXES[self.file_format.get_selected()]
        window = self.props.application.get_window()
        filename = C_("filename", "Exported Figure")

        def on_response(dialog, response):
            with contextlib.suppress(GLib.GError):
                file = dialog.save_finish(response)
                with file_io.open_wrapped(file, "wb") as wrapper:
                    window.get_canvas().figure.savefig(
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
                    window.add_toast(toast)
                    self.close()

        dialog = Gtk.FileDialog()
        dialog.set_initial_name(f"{filename}.{file_suffixes[0]}")
        dialog.set_accept_label(_("Export"))
        dialog.set_filters(
            utilities.create_file_filters([(
                self.file_format.get_selected_item().get_string(),
                file_suffixes,
            )]),
        )
        dialog.save(window, None, on_response)
