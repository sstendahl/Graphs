# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
from gettext import gettext as _

from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import misc, styles, ui, utilities


def _get_widget_factory(window):
    factory = Gtk.SignalListItemFactory.new()
    factory.connect("setup", lambda _f, i: i.set_child(styles.StylePreview()))
    factory.connect("bind", _on_bind, window)
    return factory


def _on_bind(_factory, item, window):
    widget = item.get_child()
    style = item.get_item()
    widget.style = style
    if style.get_mutable() and not widget.edit_button.get_visible():
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
    hide_unselected = Gtk.Template.Child()
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

    style_overview = Gtk.Template.Child()
    navigation_view = Gtk.Template.Child()
    grid_view = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    style_name = Gtk.Template.Child()

    figure_settings = GObject.Property(type=Graphs.FigureSettings)

    def __init__(self, application, highlighted=None):
        figure_settings = application.get_data().get_figure_settings()
        super().__init__(
            application=application, transient_for=application.get_window(),
            figure_settings=figure_settings,
        )
        notifiers = ("custom_style", "use_custom_style")
        for prop in notifiers:
            figure_settings.connect(
                "notify::" + prop.replace("_", "-"),
                getattr(self, "_on_" + prop),
            )

        ignorelist = list(notifiers) + ["min_selected", "max_selected"]
        for direction in misc.DIRECTIONS:
            ignorelist.append(f"min_{direction}")
            ignorelist.append(f"max_{direction}")

        ui.bind_values_to_object(figure_settings, self, ignorelist=ignorelist)
        self.set_axes_entries()
        if highlighted is not None:
            getattr(self, highlighted).grab_focus()
        style_manager = application.get_figure_style_manager()
        style_manager.connect("add-style", self.set_index)
        self.style_editor = styles.StyleEditor(self)
        self.grid_view.set_factory(_get_widget_factory(self))
        self.grid_view.get_model().set_model(
            style_manager.get_style_model(),
        )
        self._on_use_custom_style(figure_settings, None)
        self.present()

    def _on_use_custom_style(self, figure_settings, _a) -> None:
        if figure_settings.get_use_custom_style():
            self._on_custom_style(figure_settings, None)
        else:
            self.style_name.set_text(_("System"))
            self.grid_view.get_model().set_selected(0)

    def _on_custom_style(self, figure_settings, _a) -> None:
        if figure_settings.get_use_custom_style():
            selection_model = self.grid_view.get_model()
            stylename = figure_settings.get_custom_style()
            self.style_name.set_text(stylename)
            for index, style in enumerate(selection_model):
                if index > 0 and style.get_name() == stylename:
                    selection_model.set_selected(index)
                    break

    @Gtk.Template.Callback()
    def on_select(self, model, _pos, _n_items):
        figure_settings = self.props.figure_settings
        selected_item = model.get_selected_item()
        # Don't trigger unneccesary reloads
        if selected_item.get_file() is None:  # System style
            if figure_settings.get_use_custom_style():
                figure_settings.set_use_custom_style(False)
                self.style_name.set_text(_("System"))
        else:
            stylename = selected_item.get_name()
            if stylename != figure_settings.get_custom_style():
                figure_settings.set_custom_style(stylename)
                self.style_name.set_text(stylename)
            if not figure_settings.get_use_custom_style():
                figure_settings.set_use_custom_style(True)

    def set_axes_entries(self):
        visible_axes = self.get_application().get_data().get_used_positions()
        for (direction, visible) in zip(misc.DIRECTIONS, visible_axes):
            if visible:
                for s in ("min_", "max_"):
                    entry = getattr(self, s + direction)
                    entry.set_text(str(self.props.figure_settings.get_property(
                        s + direction,
                    )))
                    entry.connect(
                        "notify::text", self.on_entry_change, s + direction,
                    )
            # Get the label for each direction, use directional prefix if
            # two opposite X/Y axes are used simultaniously.
            labels = {
                "top": {
                    "min": _("Top X Axis Minimum") if visible_axes[0]
                    and visible_axes[1] else _("X Axis Minimum"),
                    "max": _("Top X Axis Maximum") if visible_axes[0]
                    and visible_axes[1] else _("X Axis Maximum"),
                    "scale": _("Top X Axis Scale") if visible_axes[0]
                    and visible_axes[1] else _("X Axis Scale"),
                    "label": _("Top X Axis Label") if visible_axes[0]
                    and visible_axes[1] else _("X Axis Label"),
                },
                "bottom": {
                    "min": _("Bottom X Axis Minimum") if visible_axes[0]
                    and visible_axes[1] else _("X Axis Minimum"),
                    "max": _("Bottom X Axis Maximum") if visible_axes[0]
                    and visible_axes[1] else _("X Axis Maximum"),
                    "scale": _("Bottom X Axis Scale") if visible_axes[0]
                    and visible_axes[1] else _("X Axis Scale"),
                    "label": _("Bottom X Axis Label") if visible_axes[0]
                    and visible_axes[1] else _("X Axis Label"),
                },
                "left": {
                    "min": _("Left Y Axis Minimum") if visible_axes[2]
                    and visible_axes[3] else _("Y Axis Minimum"),
                    "max": _("Left Y Axis Maximum") if visible_axes[2]
                    and visible_axes[3] else _("Y Axis Maximum"),
                    "scale": _("Left Y Axis Scale") if visible_axes[2]
                    and visible_axes[3] else _("Y Axis Scale"),
                    "label": _("Left Y Axis Label") if visible_axes[2]
                    and visible_axes[3] else _("Y Axis Label"),
                },
                "right": {
                    "min": _("Right Y Axis Minimum") if visible_axes[2]
                    and visible_axes[3] else _("Y Axis Minimum"),
                    "max": _("Right Y Axis Maximum") if visible_axes[2]
                    and visible_axes[3] else _("Y Axis Maximum"),
                    "scale": _("Right Y Axis Scale") if visible_axes[2]
                    and visible_axes[3] else _("Y Axis Scale"),
                    "label": _("Right Y Axis Label") if visible_axes[2]
                    and visible_axes[3] else _("Y Axis Label"),
                },
            }

            getattr(self, f"min_{direction}").set_title(
                labels[direction]["min"])
            getattr(self, f"max_{direction}").set_title(
                labels[direction]["max"])
            getattr(self, f"{direction}_scale").set_title(
                labels[direction]["scale"])
            getattr(self, f"{direction}_label").set_title(
                labels[direction]["label"])
            getattr(self, direction + "_limits").set_visible(visible)
            getattr(self, direction + "_scale").set_visible(visible)
            getattr(self, direction + "_label").set_visible(visible)

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
            style_manager = self.get_application().get_figure_style_manager()
            style_manager._on_style_change()

    def set_index(self, style_manager, name):
        if not self.props.figure_settings.get_use_custom_style():
            return

        old_style = self.props.figure_settings.get_custom_style()
        if old_style not in style_manager.get_stylenames():
            self.props.figure_settings.set_custom_style(name)

        selection_model = self.grid_view.get_model()
        stylename = self.props.figure_settings.get_custom_style()
        for index, style in enumerate(selection_model):
            if index > 0 and style.get_name() == stylename:
                selection_model.set_selected(index)
                break

    @Gtk.Template.Callback()
    def choose_style(self, _button):
        self.navigation_view.push(self.style_overview)

    @Gtk.Template.Callback()
    def add_style(self, _button):
        styles.AddStyleWindow(self)

    @Gtk.Template.Callback()
    def on_close(self, *_args):
        self.style_editor.save_style()
        data = self.get_application().get_data()
        data.add_view_history_state()
        data.add_history_state()
        self.destroy()

    @Gtk.Template.Callback()
    def on_set_as_default(self, _button):
        figure_settings = self.props.figure_settings
        settings = self.get_application().get_settings_child("figure")
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
        self.toast_overlay.add_toast(Adw.Toast(title=_("Defaults Updated")))
