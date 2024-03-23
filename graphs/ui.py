# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import datetime
import logging
from gettext import dgettext as N_, gettext as _, pgettext as C_

from gi.repository import Adw, GLib, Gio, Graphs, Gtk

from graphs import actions, file_import, file_io, misc, utilities
from graphs.item_box import ItemBox


def on_items_change(
    data, _ignored, application: Graphs.Application,
) -> None:
    data = application.get_data()
    item_list = application.get_window().get_item_list()
    while item_list.get_last_child() is not None:
        item_list.remove(item_list.get_last_child())

    for index, item in enumerate(data):
        itembox = ItemBox(application, item, index)
        item_list.append(itembox)
        row = item_list.get_row_at_index(index)
        row.add_controller(itembox.drag_source)
        row.add_controller(itembox.drop_source)
        row.add_controller(itembox.click_gesture)
    data.add_view_history_state()


def enable_axes_actions(
    _object, _callback, application: Graphs.Application,
) -> None:
    visible_axes = application.get_data().get_used_positions()
    menu = Gio.Menu.new()
    toggle_section = Gio.Menu.new()
    toggle_item = Gio.MenuItem.new(_("Toggle Sidebar"), "app.toggle_sidebar")
    toggle_section.append_item(toggle_item)
    optimize_section = Gio.Menu.new()
    optimize_item = Gio.MenuItem.new(
        _("Optimize Limits"), "app.optimize_limits")
    optimize_section.append_item(optimize_item)
    menu.append_section(None, toggle_section)
    menu.append_section(None, optimize_section)

    section = Gio.Menu.new()
    for index, direction in enumerate(misc.DIRECTIONS):
        if not visible_axes[index]:
            continue
        scale_section = Gio.Menu.new()
        scales = \
            ["Linear", "Logarithmic", "Radians", "Square Root", "Inverse Root"]
        for i, scale in enumerate(scales):
            scale_item = \
                Gio.MenuItem.new(_(scale), f"app.change-{direction}-scale")
            scale_item.set_attribute_value(
                "target", GLib.Variant.new_string(str(i)))
            scale_section.append_item(scale_item)
        label = _("X Axis Scale") if direction in {"top", "bottom"} \
            else _("Y Axis Scale")
        if direction == "top" and visible_axes[0] and visible_axes[1]:
            label = _("Top X Axis Scale")
        elif direction == "bottom" and visible_axes[0] and visible_axes[1]:
            label = _("Bottom X Axis Scale")
        elif direction == "left" and visible_axes[2] and visible_axes[3]:
            label = _("Left Y Axis Scale")
        elif direction == "right" and visible_axes[2] and visible_axes[3]:
            label = _("Right Y Axis Scale")

        section.append_submenu(label, scale_section)
    menu.append_section(None, section)
    application.get_window().get_view_menu_button().set_menu_model(menu)


def on_items_ignored(
    _data, _ignored, ignored: str, application: Graphs.Application,
) -> str:
    application.get_window().add_toast_string(
        N_(
            "Items {items} already exist",
            "Item {items} already exists",
            len(ignored),
        ).format(items=ignored),
    )


_GRAPHS_PROJECT_FILE_FILTER_TEMPLATE = \
    (C_("file-filter", "Graphs Project File"), ["graphs"])
_GRAPHS_PROJECT_FILE_ONLY_FILE_FILTER = utilities.create_file_filters((
    _GRAPHS_PROJECT_FILE_FILTER_TEMPLATE,
))


def add_data_dialog(application: Graphs.Application) -> None:
    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            file_import.import_from_files(
                application, dialog.open_multiple_finish(response),
            )
    dialog = Gtk.FileDialog()
    dialog.set_filters(
        utilities.create_file_filters((
            (
                C_("file-filter", "Supported files"),
                ["xy", "dat", "txt", "csv", "xrdml", "xry", "graphs"],
            ),
            (C_("file-filter", "ASCII files"), ["xy", "dat", "txt", "csv"]),
            (C_("file-filter", "PANalytical XRDML"), ["xrdml"]),
            (C_("file-filter", "Leybold xry"), ["xry"]),
            _GRAPHS_PROJECT_FILE_FILTER_TEMPLATE,
        )),
    )
    dialog.open_multiple(application.get_window(), None, on_response)


def save_project_dialog(application: Graphs.Application) -> None:

    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            data = application.get_data()
            data.props.project_file = dialog.save_finish(response)
            data.save()
            data.props.unsaved = False
            application.emit("project-saved")
    dialog = Gtk.FileDialog()
    dialog.set_filters(_GRAPHS_PROJECT_FILE_ONLY_FILE_FILTER)
    dialog.set_initial_name("project.graphs")
    dialog.save(application.get_window(), None, on_response)


def open_project_dialog(application: Graphs.Application) -> None:
    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            application.get_data().props.project_file = \
                dialog.open_finish(response)
            application.get_data().load()
    dialog = Gtk.FileDialog()
    dialog.set_filters(_GRAPHS_PROJECT_FILE_ONLY_FILE_FILTER)
    dialog.open(application.get_window(), None, on_response)


def export_data_dialog(application: Graphs.Application) -> None:
    data = application.get_data()
    window = application.get_window()
    if data.props.empty:
        window.add_toast_string(_("No data to export"))
        return
    multiple = len(data) > 1

    def on_response(dialog, response):
        with contextlib.suppress(GLib.GError):
            if multiple:
                directory = dialog.select_folder_finish(response)
                for item in data:
                    file = directory.get_child_for_display_name(
                        f"{item.get_name()}.txt")
                    file_io.save_item(file, item)
            else:
                file = dialog.save_finish(response)
                file_io.save_item(file, data[0])
            action = Gio.SimpleAction.new(
                "open-file-location", None,
            )
            action.connect("activate", actions.open_file_location, file)
            application.add_action(action)
            toast = Adw.Toast.new(_("Exported Data"))
            toast.set_button_label(_("Open Location"))
            toast.set_action_name("app.open-file-location")
            window.add_toast(toast)
    dialog = Gtk.FileDialog()
    if multiple:
        dialog.select_folder(window, None, on_response)
    else:
        filename = f"{data[0].get_name()}.txt"
        dialog.set_initial_name(filename)
        dialog.set_filters(
            utilities.create_file_filters((
                (C_("file-filter", "Text Files"), ["txt"]),
            )),
        )
        dialog.save(window, None, on_response)


def build_dialog(name: str):
    return Gtk.Builder.new_from_resource(
        "/se/sjoerd/Graphs/ui/dialogs.ui",
    ).get_object(name)


def show_about_dialog(application: Graphs.Application) -> str:
    file = Gio.File.new_for_uri("resource:///se/sjoerd/Graphs/whats_new")
    copyright_text = \
        f"© 2022 – {datetime.date.today().year} {application.get_author()}"
    Adw.AboutDialog(
        application_name=_("Graphs"),
        application_icon=application.get_application_id(),
        website=application.get_website(),
        developer_name=application.get_author(),
        issue_url=application.get_issues(),
        version=application.get_version(), developers=[
            "Sjoerd Stendahl <contact@sjoerd.se>",
            "Christoph Kohnen <christoph.kohnen@disroot.org>",
        ],
        designers=[
            "Sjoerd Stendahl <contact@sjoerd.se>",
            "Christoph Kohnen <christoph.kohnen@disroot.org>",
            "Tobias Bernard <tbernard@gnome.org>",
        ],
        copyright=copyright_text,
        license_type="GTK_LICENSE_GPL_3_0",
        translator_credits=_("translator-credits"),
        release_notes=file.load_bytes(None)[0].get_data().decode("utf-8"),
    ).present(application.get_window())


def load_values_from_dict(window, values: dict, ignorelist=None) -> None:
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
                logging.warn(
                    _("Unsupported Widget {widget}")
                    .format(widget=type(widget)),
                )
        except AttributeError:
            logging.warn(_("No way to apply “{key}”").format(key=key))


def save_values_to_dict(window, keys: list, ignorelist=None) -> None:
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


def bind_values_to_settings(
    settings, window, prefix="", ignorelist=None,
) -> None:
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
                logging.warn(
                    _("Unsupported Widget {widget}")
                    .format(widget=type(widget)),
                )
        except AttributeError:
            logging.warn(_("No way to apply “{key}”").format(key=key))


def bind_values_to_object(source, window, ignorelist=None) -> None:
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
                logging.warn(
                    _("Unsupported Widget {widget}")
                    .format(widget=type(widget)),
                )
        except AttributeError:
            logging.warn(_("No way to apply “{key}”").format(key=key))
    return bindings
