# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
from gettext import gettext as _

from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import misc, styles, ui, utilities

_DIRECTIONS = ["bottom", "left", "top", "right"]


def _get_widget_factory(window):
    factory = Gtk.SignalListItemFactory.new()
    factory.connect("setup", _on_setup)
    factory.connect("bind", _on_bind, window)
    return factory


def _on_setup(_factory, item):
    widget = styles.StylePreview()
    item.set_child(widget)


def _on_bind(_factoy, item, window):
    widget = item.get_child()
    style = item.get_item()
    style.bind_property("name", widget.label, "label", 2)
    style.bind_property("preview", widget.picture, "file", 2)
    style_manager = window.get_application().get_figure_style_manager()
    if style.name in style_manager.get_user_styles():
        widget.edit_button.set_visible(True)
        widget.edit_button.connect("clicked", window.edit_style, style)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/figure_settings.ui")
class FigureSettingsWindow(Adw.Window):
    __gtype_name__ = "GraphsFigureSettingsWindow"

    title = Gtk.Template.Child()
    bottom_label = Gtk.Template.Child()
    left_label = Gtk.Template.Child()
    top_label = Gtk.Template.Child()
    right_label = Gtk.Template.Child()
    bottom_scale = Gtk.Template.Child()
    left_scale = Gtk.Template.Child()
    top_scale = Gtk.Template.Child()
    right_scale = Gtk.Template.Child()
    legend = Gtk.Template.Child()
    legend_position = Gtk.Template.Child()
    min_left = Gtk.Template.Child()
    max_left = Gtk.Template.Child()
    min_bottom = Gtk.Template.Child()
    max_bottom = Gtk.Template.Child()
    min_right = Gtk.Template.Child()
    max_right = Gtk.Template.Child()
    min_top = Gtk.Template.Child()
    max_top = Gtk.Template.Child()

    no_data_message = Gtk.Template.Child()
    style_overview = Gtk.Template.Child()
    navigation_view = Gtk.Template.Child()
    grid_view = Gtk.Template.Child()

    figure_settings = GObject.Property(type=Graphs.FigureSettings)

    def __init__(self, application, highlighted=None):
        super().__init__(
            application=application, transient_for=application.get_window(),
            figure_settings=application.get_data().get_figure_settings(),
        )

        ignorelist = [
            "custom_style", "min_selected", "max_selected", "use_custom_style",
        ]
        for direction in _DIRECTIONS:
            ignorelist.append(f"min_{direction}")
            ignorelist.append(f"max_{direction}")

        ui.bind_values_to_object(
            self.props.figure_settings, self, ignorelist=ignorelist,
        )
        self.set_axes_entries()
        self.no_data_message.set_visible(
            self.get_application().get_data().is_empty(),
        )
        if highlighted is not None:
            getattr(self, highlighted).grab_focus()
        self.present()

        self.style_editor = styles.StyleEditor(self)
        #self.navigation_view.add(self.style_editor)
        self.grid_view.set_factory(_get_widget_factory(self))
        style_manager = application.get_figure_style_manager()
        self.grid_view.get_model().set_model(
            style_manager.get_available_stylenames(),
        )

    def set_axes_entries(self):
        used_axes = [[direction, False] for direction in _DIRECTIONS]
        for item in self.get_application().get_data():
            for i in item.get_xposition() * 2, 1 + item.get_yposition() * 2:
                used_axes[i][1] = True
        for (direction, visible) in used_axes:
            if visible:
                for s in ["min_", "max_"]:
                    entry = getattr(self, s + direction)
                    entry.set_visible(True)
                    entry.set_text(str(self.props.figure_settings.get_property(
                        s + direction,
                    )))
                    entry.connect(
                        "notify::text", self.on_entry_change, s + direction,
                    )

    def on_entry_change(self, entry, _param, prop):
        with contextlib.suppress(SyntaxError):
            self.props.figure_settings.set_property(
                prop, utilities.string_to_float(entry.get_text()),
            )

    def edit_style(self, _button, style):
        self.style_editor.load_style(style)
        self.navigation_view.push(self.style_editor)

    @Gtk.Template.Callback()
    def on_pop(self, _view, page):
        if page == self.style_editor:
            self.style_editor.save_style()

    @Gtk.Template.Callback()
    def choose_style(self, _button):
        self.navigation_view.push(self.style_overview)

    @Gtk.Template.Callback()
    def add_style(self, _button):
        styles.AddStyleWindow(self)

    @Gtk.Template.Callback()
    def on_close(self, *_args):
        self.style_editor.save_style()
        self.get_application().get_data().add_view_history_state()
        self.destroy()

    @Gtk.Template.Callback()
    def on_set_as_default(self, _button):
        figure_settings = self.props.figure_settings
        settings = self.get_application().get_settings("figure")
        ignorelist = ["min_selected", "max_selected"] + misc.LIMITS
        for prop in dir(figure_settings.props):
            if prop not in ignorelist:
                value = figure_settings.get_property(prop)
                prop = prop.replace("_", "-")
                if isinstance(value, str):
                    settings.set_string(prop, value)
                elif isinstance(value, bool):
                    settings.set_boolean(prop, value)
                elif isinstance(value, int):
                    settings.set_enum(prop, value)
        self.add_toast(Adw.Toast(title=_("Defaults Updated")))
