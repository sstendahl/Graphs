# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
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
    developers = [
        "Sjoerd Stendahl <contact@sjoerd.se>",
        "Christoph Kohnen <christoph.kohnen@disroot.org>",
    ]
    about = Adw.AboutWindow(transient_for=self.main_window,
                            application_name=self.name,
                            application_icon=self.props.application_id,
                            website=self.website,
                            developer_name=self.author,
                            issue_url=self.issues,
                            version=self.version,
                            developers=developers,
                            copyright=f"© {self.copyright} {self.author}",
                            license_type="GTK_LICENSE_GPL_3_0")
    about.set_translator_credits(_("translator-credits"))
    whats_new_file = Gio.File.new_for_uri(
        "resource:///se/sjoerd/Graphs/whats_new")
    release_notes = whats_new_file.load_bytes(None)[0].get_data()
    about.set_release_notes(release_notes.decode("utf-8"))
    about.present()
