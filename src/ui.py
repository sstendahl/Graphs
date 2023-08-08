# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import datetime
import logging
from gettext import gettext as _

from gi.repository import Adw, GLib, Gio, Gtk

from graphs import file_import, file_io, graphs, utilities
from graphs.item import Item
from graphs.item_box import ItemBox


def on_style_change(_shortcut, _theme, _widget, self):
    graphs.reload(self)


def set_clipboard_buttons(self):
    """
    Enable and disable the buttons for the undo and redo buttons and backwards
    and forwards view.
    """
    self.main_window.view_forward_button.set_sensitive(
        self.ViewClipboard.clipboard_pos < - 1)
    self.main_window.view_back_button.set_sensitive(
        abs(self.ViewClipboard.clipboard_pos)
        < len(self.ViewClipboard.clipboard))
    self.main_window.undo_button.set_sensitive(
        abs(self.Clipboard.clipboard_pos) < len(self.Clipboard.clipboard))
    self.main_window.redo_button.set_sensitive(
        self.Clipboard.clipboard_pos < - 1)


def enable_data_dependent_buttons(self):
    enabled = False
    for item in self.datadict.values():
        if item.selected and isinstance(item, Item):
            enabled = True
    self.main_window.shift_vertically_button.set_sensitive(enabled)


def reload_item_menu(self):
    while self.main_window.item_list.get_last_child() is not None:
        self.main_window.item_list.remove(
            self.main_window.item_list.get_last_child())

    for item in self.datadict.values():
        self.main_window.item_list.append(ItemBox(self, item))


def add_data_dialog(self):
    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            file_import.prepare_import(
                self, dialog.open_multiple_finish(response))
    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters([
            (_("ASCII files"), ["xy", "dat", "txt", "csv"]),
            (_("PANalytical XRDML"), ["xrdml"]),
            (_("Leybold xry"), ["xry"]),
        ]),
    )
    dialog.open_multiple(self.main_window, None, on_response)


def save_project_dialog(self):
    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            file = dialog.save_finish(response)
            file_io.save_project(
                file, self.plot_settings, self.datadict, self.Clipboard,
                self.ViewClipboard, self.version)
    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters([(_("Graphs Project File"),
                                      ["graphs"])]))
    dialog.set_initial_name("project.graphs")
    dialog.save(self.main_window, None, on_response)


def open_project_dialog(self):
    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            file = dialog.open_finish(response)
            graphs.open_project(self, file)
    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters([(_("Graphs Project File"),
                                      ["graphs"])]))
    dialog.open(self.main_window, None, on_response)


def export_data_dialog(self):
    if not self.datadict:
        return
    multiple = len(self.datadict) > 1

    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            if multiple:
                directory = dialog.select_folder_finish(response)
                for item in self.datadict.values():
                    file = directory.get_child_for_display_name(
                        f"{item.name}.txt")
                    file_io.save_item(file, item)
            else:
                item = list(self.datadict.values())[0]
                file_io.save_item(dialog.save_finish(response), item)
    dialog = Gtk.FileDialog()
    if multiple:
        dialog.select_folder(self.main_window, None, on_response)
    else:
        filename = f"{list(self.datadict.values())[0].name}.txt"
        dialog.set_initial_name(filename)
        dialog.set_filters(
            utilities.create_file_filters([(_("Text Files"), ["txt"])]))
        dialog.save(self.main_window, None, on_response)


def build_dialog(name):
    return Gtk.Builder.new_from_resource(
        "/se/sjoerd/Graphs/ui/dialogs.ui").get_object(name)


def show_about_window(self):
    Adw.AboutWindow(
        transient_for=self.main_window, application_name=self.name,
        application_icon=self.props.application_id, website=self.website,
        developer_name=self.author, issue_url=self.issues,
        version=self.version, developers=[
            "Sjoerd Stendahl <contact@sjoerd.se>",
            "Christoph Kohnen <christoph.kohnen@disroot.org>",
        ],
        copyright=f"© 2022 – {datetime.date.today().year} {self.author}",
        license_type="GTK_LICENSE_GPL_3_0",
        translator_credits=_("translator-credits"),
        release_notes=file_io.read_file(
            Gio.File.new_for_uri("resource:///se/sjoerd/Graphs/whats_new")),
    ).present()


def load_values_from_dict(window, values: dict):
    for key, value in values.items():
        try:
            widget = getattr(window, key)
            if isinstance(widget, Adw.EntryRow):
                widget.set_text(str(value))
            elif isinstance(widget, Adw.ComboRow):
                utilities.set_chooser(widget, value)
            elif isinstance(widget, Gtk.SpinButton):
                widget.set_value(value)
            elif isinstance(widget, Gtk.Switch):
                widget.set_active(bool(value))
            elif isinstance(widget, Adw.ExpanderRow):
                widget.set_enable_expansion(bool(value))
                widget.set_expanded(bool(value))
            elif isinstance(widget, Gtk.Scale):
                widget.set_value(value)
            elif isinstance(widget, Gtk.Button):
                widget.color = value
            else:
                logging.warn(_("Unsupported Widget {}").format(type(widget)))
        except AttributeError:
            logging.warn(_("No way to apply “{}”").format(key))


def save_values_to_dict(window, keys: list):
    values = {}
    for key in keys:
        with contextlib.suppress(AttributeError):
            widget = getattr(window, key)
            if isinstance(widget, Adw.EntryRow):
                values[key] = str(widget.get_text())
            elif isinstance(widget, Adw.ComboRow):
                values[key] = utilities.get_selected_chooser_item(widget)
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


def bind_values_to_settings(settings, window):
    for key in settings.props.settings_schema.list_keys():
        try:
            widget = getattr(window, key.replace("-", "_"))
            if isinstance(widget, Adw.EntryRow):
                settings.bind(key, widget, "text", 0)
            elif isinstance(widget, Adw.ComboRow):
                utilities.set_chooser(widget, settings.get_string(key))
                # TODO: handle change
            elif isinstance(widget, Gtk.SpinButton):
                settings.bind(key, widget, "value", 0)
            elif isinstance(widget, Gtk.Switch):
                settings.bind(key, widget, "active", 0)
            elif isinstance(widget, Adw.ExpanderRow):
                settings.bind(key, widget, "enable-expansion", 0)
            elif isinstance(widget, Gtk.Scale):
                settings.bind(key, widget, "value", 0)
            else:
                logging.warn(_("Unsupported Widget {}").format(type(widget)))
        except AttributeError:
            logging.warn(_("No way to apply “{}”").format(key))
