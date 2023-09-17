# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
from gettext import gettext as _

from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import misc, styles, ui, utilities

_DIRECTIONS = ["bottom", "left", "top", "right"]


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/figure_settings.ui")
class FigureSettingsWindow(Adw.PreferencesWindow):
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
    use_custom_style = Gtk.Template.Child()
    custom_style = Gtk.Template.Child()
    min_left = Gtk.Template.Child()
    max_left = Gtk.Template.Child()
    min_bottom = Gtk.Template.Child()
    max_bottom = Gtk.Template.Child()
    min_right = Gtk.Template.Child()
    max_right = Gtk.Template.Child()
    min_top = Gtk.Template.Child()
    max_top = Gtk.Template.Child()

    no_data_message = Gtk.Template.Child()

    figure_settings = GObject.Property(type=Graphs.FigureSettings)

    def __init__(self, application, highlighted=None):
        super().__init__(
            application=application, transient_for=application.get_window(),
            figure_settings=application.get_data().get_figure_settings(),
        )

        ignorelist = ["custom_style", "min_selected", "max_selected"]
        for direction in _DIRECTIONS:
            ignorelist.append(f"min_{direction}")
            ignorelist.append(f"max_{direction}")

        ui.bind_values_to_object(
            self.props.figure_settings, self, ignorelist=ignorelist,
        )
        styles_ = sorted(styles.get_user_styles(application).keys())
        style_index = styles_.index(
            self.props.figure_settings.get_custom_style())
        self.custom_style.set_model(Gtk.StringList.new(styles_))
        self.custom_style.set_selected(style_index)

        self.set_axes_entries()
        self.no_data_message.set_visible(
            self.get_application().get_data().is_empty(),
        )
        if highlighted is not None:
            getattr(self, highlighted).grab_focus()
        self.present()

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

    @Gtk.Template.Callback()
    def on_close(self, *_args):
        self.get_application().get_data().add_view_history_state()
        self.destroy()

    @Gtk.Template.Callback()
    def on_custom_style_select(self, comborow, _ignored):
        selected_style = comborow.get_selected_item().get_string()
        if selected_style != self.props.figure_settings.get_custom_style():
            self.props.figure_settings.set_custom_style(selected_style)

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
