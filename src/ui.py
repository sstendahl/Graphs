# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import datetime
import logging
from gettext import gettext as _

from gi.repository import Adw, GLib, Gio, Gtk

from graphs import file_import, file_io, project, styles, utilities
from graphs.canvas import Canvas
from graphs.item_box import ItemBox

from matplotlib import pyplot


def on_figure_style_change(_a, _b, self):
    if not self.get_settings(
            "general").get_boolean("override-item-properties"):
        reload_canvas(self)
        return
    styles.update(self)
    color_cycle = pyplot.rcParams["axes.prop_cycle"].by_key()["color"]
    for item in self.get_data():
        item.reset()
    count = 0
    for item in self.get_data():
        if item.__gtype_name__ == "GraphsDataItem":
            if count > len(color_cycle):
                count = 0
            item.props.color = color_cycle[count]
            count += 1
    reload_canvas(self)


def on_items_change(data, _ignored, self):
    item_list = self.get_window().get_item_list()
    while item_list.get_last_child() is not None:
        item_list.remove(item_list.get_last_child())

    for item in self.get_data():
        item_list.append(ItemBox(self, item))
    item_list.set_visible(not data.is_empty())
    self.get_view_clipboard().add()


def on_items_ignored(_data, _ignored, ignored, self):
    if len(ignored) > 1:
        toast = _("Items {} already exist").format(ignored)
    else:
        toast = _("Item {} already exists")
    self.get_window().add_toast_string(toast)


def set_clipboard_buttons(self):
    """
    Enable and disable the buttons for the undo and redo buttons and backwards
    and forwards view.
    """
    self.get_window().get_view_forward_button().set_sensitive(
        self.get_view_clipboard().clipboard_pos < - 1)
    self.get_window().get_view_back_button().set_sensitive(
        abs(self.get_view_clipboard().clipboard_pos)
        < len(self.get_view_clipboard().clipboard))


def add_data_dialog(self):
    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            file_import.import_from_files(
                self, dialog.open_multiple_finish(response),
            )
    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters([
            (_("ASCII files"), ["xy", "dat", "txt", "csv"]),
            (_("PANalytical XRDML"), ["xrdml"]),
            (_("Leybold xry"), ["xry"]),
        ]),
    )
    dialog.open_multiple(self.get_window(), None, on_response)


def save_project_dialog(self):
    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            file = dialog.save_finish(response)
            project.save_project(self, file)
    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters([(_("Graphs Project File"),
                                      ["graphs"])]))
    dialog.set_initial_name("project.graphs")
    dialog.save(self.get_window(), None, on_response)


def open_project_dialog(self):
    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            file = dialog.open_finish(response)
            project.load_project(self, file)
    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters([(_("Graphs Project File"),
                                      ["graphs"])]))
    dialog.open(self.get_window(), None, on_response)


def export_data_dialog(self):
    if self.get_data().is_empty():
        self.get_window().add_toast_string(_("No data to export"))
        return
    multiple = len(self.get_data()) > 1

    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            if multiple:
                directory = dialog.select_folder_finish(response)
                for item in self.get_data():
                    file = directory.get_child_for_display_name(
                        f"{item.get_name()}.txt")
                    file_io.save_item(file, item)
            else:
                file_io.save_item(
                    dialog.save_finish(response), self.get_data()[0],
                )
            self.get_window().add_toast_string(_("Exported Data"))
    dialog = Gtk.FileDialog()
    if multiple:
        dialog.select_folder(self.get_window(), None, on_response)
    else:
        filename = f"{self.get_data()[0].name}.txt"
        dialog.set_initial_name(filename)
        dialog.set_filters(
            utilities.create_file_filters([(_("Text Files"), ["txt"])]))
        dialog.save(self.get_window(), None, on_response)


def build_dialog(name):
    return Gtk.Builder.new_from_resource(
        "/se/sjoerd/Graphs/ui/dialogs.ui").get_object(name)


def show_about_window(self):
    Adw.AboutWindow(
        transient_for=self.get_window(), application_name=self.get_name(),
        application_icon=self.get_application_id(), website=self.get_website(),
        developer_name=self.get_author(), issue_url=self.get_issues(),
        version=self.get_version(), developers=[
            "Sjoerd Stendahl <contact@sjoerd.se>",
            "Christoph Kohnen <christoph.kohnen@disroot.org>",
        ],
        copyright=f"© 2022 – {datetime.date.today().year} {self.get_author()}",
        license_type="GTK_LICENSE_GPL_3_0",
        translator_credits=_("translator-credits"),
        release_notes=file_io.read_file(
            Gio.File.new_for_uri("resource:///se/sjoerd/Graphs/whats_new")),
    ).present()


def load_values_from_dict(window, values: dict, ignorelist=None):
    for key, value in values.items():
        if ignorelist is not None and key in ignorelist:
            continue
        try:
            widget = getattr(window, key.replace("-", "_"))
            if isinstance(widget, Adw.EntryRow):
                widget.set_text(str(value))
            elif isinstance(widget, Adw.ComboRow):
                widget.set_selected(int(value))
            elif isinstance(widget, Gtk.SpinButton):
                widget.set_value(value)
            elif isinstance(widget, Gtk.Switch):
                widget.set_active(bool(value))
            elif isinstance(widget, Adw.ExpanderRow):
                widget.set_enable_expansion(bool(value))
                widget.set_expanded(True)
            elif isinstance(widget, Gtk.Scale):
                widget.set_value(value)
            elif isinstance(widget, Gtk.Button):
                widget.color = value
            else:
                logging.warn(_("Unsupported Widget {}").format(type(widget)))
        except AttributeError:
            logging.warn(_("No way to apply “{}”").format(key))


def save_values_to_dict(window, keys: list, ignorelist=None):
    values = {}
    for key in keys:
        if ignorelist is not None and key in ignorelist:
            continue
        with contextlib.suppress(AttributeError):
            widget = getattr(window, key.replace("-", "_"))
            if isinstance(widget, Adw.EntryRow):
                values[key] = str(widget.get_text())
            elif isinstance(widget, Adw.ComboRow):
                values[key] = widget.get_selected()
            elif isinstance(widget, Gtk.SpinButton):
                values[key] = widget.get_value()
            elif isinstance(widget, Gtk.Switch):
                values[key] = bool(widget.get_active())
            elif isinstance(widget, Adw.ExpanderRow):
                values[key] = bool(widget.get_enable_expansion())
            elif isinstance(widget, Gtk.Scale):
                values[key] = widget.get_value()
            elif isinstance(widget, Gtk.Button):
                values[key] = widget.color
    return values


def _on_settings_select(chooser, _ignored, settings, key):
    if settings.get_enum(key) != chooser.get_selected():
        settings.set_enum(key, chooser.get_selected())


def _on_settings_update(settings, key, chooser):
    chooser.set_selected(settings.get_enum(key))


def bind_values_to_settings(settings, window, prefix="", ignorelist=None):
    for key in settings.props.settings_schema.list_keys():
        if ignorelist is not None and key in ignorelist:
            continue
        try:
            widget = getattr(window, prefix + key.replace("-", "_"))
            if isinstance(widget, Adw.EntryRow):
                settings.bind(key, widget, "text", 0)
            elif isinstance(widget, Adw.ComboRow):
                widget.set_selected(settings.get_enum(key))
                settings.connect(
                    f"changed::{key}", _on_settings_update, widget)
                widget.connect(
                    "notify::selected", _on_settings_select, settings, key)
            elif isinstance(widget, Gtk.SpinButton):
                settings.bind(key, widget, "value", 0)
            elif isinstance(widget, Gtk.Switch):
                settings.bind(key, widget, "active", 0)
            elif isinstance(widget, Adw.ExpanderRow):
                settings.bind(key, widget, "enable-expansion", 0)
                widget.set_expanded(True)
            else:
                logging.warn(_("Unsupported Widget {}").format(type(widget)))
        except AttributeError:
            logging.warn(_("No way to apply “{}”").format(key))


def bind_values_to_object(source, window, ignorelist=None):
    bindings = []
    for key in dir(source.props):
        if ignorelist is not None and key in ignorelist:
            continue
        try:
            widget = getattr(window, key)
            if isinstance(widget, Adw.EntryRow):
                bindings.append(source.bind_property(
                    key, widget, "text", 1 | 2,
                ))
            elif isinstance(widget, Adw.ComboRow):
                bindings.append(source.bind_property(
                    key, widget, "selected", 1 | 2,
                ))
            elif isinstance(widget, Adw.ExpanderRow):
                bindings.append(source.bind_property(
                    key, widget, "enable-expansion", 1 | 2,
                ))
                widget.set_expanded(True)
            elif isinstance(widget, Gtk.Scale):
                bindings.append(source.bind_property(
                    key, widget.get_adjustment(), "value", 1 | 2,
                ))
            else:
                logging.warn(_("Unsupported Widget {}").format(type(widget)))
        except AttributeError:
            logging.warn(_("No way to apply “{}”").format(key))
    return bindings


def reload_canvas(self):
    """Reloads the canvas of the main window"""
    styles.update(self)
    canvas = Canvas(self)
    data = self.get_data()
    figure_settings = data.get_figure_settings()
    for prop in dir(figure_settings.props):
        if prop not in ["use_custom_style", "custom_style"]:
            figure_settings.bind_property(prop, canvas, prop, 1 | 2)
    data.bind_property("items", canvas, "items", 2)
    win = self.get_window()
    win.set_canvas(canvas)
    win.get_cut_button().bind_property(
        "sensitive", canvas, "highlight_enabled", 2,
    )
