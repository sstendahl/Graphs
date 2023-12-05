# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import datetime
import logging
import os

from gettext import gettext as _
from pathlib import Path
from urllib.parse import urlparse

from gi.repository import Adw, GLib, Gio, Gtk

from graphs import file_import, file_io, migrate, utilities
from graphs.item_box import ItemBox


def on_items_change(data, _ignored, self):
    data = self.get_data()
    data.set_unsaved(True)
    item_list = self.get_window().get_item_list()
    while item_list.get_last_child() is not None:
        item_list.remove(item_list.get_last_child())

    for index, item in enumerate(data):
        itembox = ItemBox(self, item, index)
        item_list.append(itembox)
        row = item_list.get_row_at_index(index)
        row.add_controller(itembox.drag_source)
        row.add_controller(itembox.drop_source)
    data.add_view_history_state()


def on_items_ignored(_data, _ignored, ignored, self):
    if len(ignored) > 1:
        toast = _("Items {} already exist").format(ignored)
    else:
        toast = _("Item {} already exists")
    self.get_window().add_toast_string(toast)


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


def save_project_dialog(self, require_dialog=False, close=False):
    if self.get_data().props.project_uri != "" and not require_dialog:
        file_uri = self.get_data().props.project_uri
        file = Gio.File.new_for_uri(file_uri)
        file_io.write_json(file, self.get_data().to_project_dict(), False)
        self.get_data().change_unsaved(False)
        return

    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            file = dialog.save_finish(response)
            file_io.write_json(file, self.get_data().to_project_dict(), False)
            self.get_data().change_unsaved(False)
            self.get_data().props.project_uri = file.get_uri()
            file_name = Path(file.get_basename()).stem
            uri_parse  = urlparse(self.get_data().props.project_uri)
            filepath = os.path.abspath(os.path.join(uri_parse.netloc, uri_parse.path))
            filepath = filepath.replace(os.path.expanduser("~"), "~")
            self.get_window().get_content_title().set_subtitle(filepath)
            self.get_window().get_content_title().set_title(file_name)
            if close:
                self.get_window().destroy()
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
            try:
                project_dict = file_io.parse_json(file)
            except UnicodeDecodeError:
                project_dict = migrate.migrate_project(file)
            project_uri = file.get_uri()
            self.get_data().load_from_project_dict(project_dict, project_uri)
    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters([(_("Graphs Project File"),
                                      ["graphs"])]))
    dialog.open(self.get_window(), None, on_response)


def export_data_dialog(self):
    if self.get_data().props.unsaved:
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
        filename = f"{self.get_data()[0].get_name()}.txt"
        dialog.set_initial_name(filename)
        dialog.set_filters(
            utilities.create_file_filters([(_("Text Files"), ["txt"])]))
        dialog.save(self.get_window(), None, on_response)


def build_dialog(name):
    return Gtk.Builder.new_from_resource(
        "/se/sjoerd/Graphs/ui/dialogs.ui").get_object(name)


def show_about_window(self):
    file = Gio.File.new_for_uri("resource:///se/sjoerd/Graphs/whats_new")
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
        release_notes=file.load_bytes(None)[0].get_data().decode("utf-8"),
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
            elif isinstance(widget, Gtk.Switch):
                widget.set_active(bool(value))
            elif isinstance(widget, Adw.ExpanderRow):
                widget.set_enable_expansion(bool(value))
                widget.set_expanded(True)
            elif isinstance(widget, Gtk.Scale):
                widget.set_value(value)
            elif isinstance(widget, Gtk.Button):
                widget.color = value
            elif isinstance(widget, Adw.SwitchRow):
                widget.set_active(bool(value))
            elif isinstance(widget, Adw.SpinRow):
                widget.set_value(value)
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
            elif isinstance(widget, Gtk.Switch):
                values[key] = bool(widget.get_active())
            elif isinstance(widget, Adw.ExpanderRow):
                values[key] = bool(widget.get_enable_expansion())
            elif isinstance(widget, Gtk.Scale):
                values[key] = widget.get_value()
            elif isinstance(widget, Gtk.Button):
                values[key] = widget.color
            elif isinstance(widget, Adw.SwitchRow):
                values[key] = bool(widget.get_active())
            elif isinstance(widget, Adw.SpinRow):
                values[key] = widget.get_value()
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
            elif isinstance(widget, Gtk.Switch):
                settings.bind(key, widget, "active", 0)
            elif isinstance(widget, Adw.ExpanderRow):
                settings.bind(key, widget, "enable-expansion", 0)
                widget.set_expanded(True)
            elif isinstance(widget, Adw.SwitchRow):
                settings.bind(key, widget, "active", 0)
            elif isinstance(widget, Adw.SpinRow):
                settings.bind(key, widget, "value", 0)
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
            elif isinstance(widget, Adw.SwitchRow):
                bindings.append(source.bind_property(
                    key, widget, "active", 1 | 2,
                ))
            else:
                logging.warn(_("Unsupported Widget {}").format(type(widget)))
        except AttributeError:
            logging.warn(_("No way to apply “{}”").format(key))
    return bindings
