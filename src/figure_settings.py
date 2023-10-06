# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
from gettext import gettext as _

from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import misc, styles, ui, utilities

_DIRECTIONS = ["bottom", "left", "top", "right"]


def _get_widget_factory(window):
    factory = Gtk.SignalListItemFactory.new()
    factory.connect("setup", lambda _f, i: i.set_child(styles.StylePreview()))
    factory.connect("bind", _on_bind, window)
    return factory


def _on_bind(_factory, item, window):
    widget = item.get_child()
    style = item.get_item()
    widget.style = style
    if style.mutable:
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
    left_limits = Gtk.Template.Child()
    right_limits = Gtk.Template.Child()
    bottom_limits = Gtk.Template.Child()
    top_limits = Gtk.Template.Child()
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

        self.style_editor = styles.StyleEditor(self)
        self.grid_view.set_factory(_get_widget_factory(self))
        style_model = application.get_figure_style_manager().get_style_model()
        selection_model = self.grid_view.get_model()
        selection_model.set_model(style_model)
        if self.props.figure_settings.get_use_custom_style():
            stylename = self.props.figure_settings.get_custom_style()
            for index in range(style_model.get_n_items()):
                style = style_model.get_item(index)
                if index > 0 and style.name == stylename:
                    selection_model.set_selected(index)
                    break
        else:
            selection_model.set_selected(0)

        self.present()

    @Gtk.Template.Callback()
    def on_select(self, model, _pos, _n_items):
        figure_settings = self.props.figure_settings
        selected_item = model.get_selected_item()
        # Don't trigger unneccesary reloads
        if selected_item.file is None:  # System style
            if figure_settings.get_use_custom_style():
                figure_settings.set_use_custom_style(False)
        else:
            if selected_item.name != figure_settings.get_custom_style():
                figure_settings.set_custom_style(selected_item.name)
            if not figure_settings.get_use_custom_style():
                figure_settings.set_use_custom_style(True)

    def set_axes_entries(self):
        used_axes = [[direction, False] for direction in _DIRECTIONS]
        for item in self.get_application().get_data():
            for i in item.get_xposition() * 2, 1 + item.get_yposition() * 2:
                used_axes[i][1] = True
        for (direction, visible) in used_axes:
            if visible:
                for s in ["min_", "max_"]:
                    entry = getattr(self, s + direction)
                    entry.set_text(str(self.props.figure_settings.get_property(
                        s + direction,
                    )))
                    entry.connect(
                        "notify::text", self.on_entry_change, s + direction,
                    )
                getattr(self, direction + "_limits").set_visible(True)

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
