# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib

from gi.repository import Adw, GObject, Gtk

from graphs import misc, styles, ui, utilities


class FigureSettings(GObject.Object):
    __gtype_name__ = "FigureSettings"

    title = GObject.Property(type=str, default="")
    bottom_label = GObject.Property(type=str, default="")
    left_label = GObject.Property(type=str, default="")
    top_label = GObject.Property(type=str, default="")
    right_label = GObject.Property(type=str, default="")

    bottom_scale = GObject.Property(type=int, default=0)
    left_scale = GObject.Property(type=int, default=0)
    top_scale = GObject.Property(type=int, default=0)
    right_scale = GObject.Property(type=int, default=0)

    legend = GObject.Property(type=bool, default=True)
    legend_position = GObject.Property(type=int, default=0)
    use_custom_style = GObject.Property(type=bool, default=False)
    custom_style = GObject.Property(type=str, default="adwaita")

    min_bottom = GObject.Property(type=float, default=0)
    max_bottom = GObject.Property(type=float, default=1)
    min_left = GObject.Property(type=float, default=0)
    max_left = GObject.Property(type=float, default=10)
    min_top = GObject.Property(type=float, default=0)
    max_top = GObject.Property(type=float, default=1)
    min_right = GObject.Property(type=float, default=0)
    max_right = GObject.Property(type=float, default=10)

    min_selected = GObject.Property(type=float, default=0)
    max_selected = GObject.Property(type=float, default=0)

    @staticmethod
    def new(settings):
        return FigureSettings(
            bottom_scale=settings.get_enum("bottom-scale"),
            left_scale=settings.get_enum("left-scale"),
            right_scale=settings.get_enum("right-scale"),
            top_scale=settings.get_enum("top-scale"),
            title=settings.get_string("title"),
            bottom_label=settings.get_string("bottom-label"),
            left_label=settings.get_string("left-label"),
            top_label=settings.get_string("top-label"),
            right_label=settings.get_string("right-label"),
            legend=settings.get_boolean("legend"),
            use_custom_style=settings.get_boolean("use-custom-style"),
            legend_position=settings.get_enum("legend-position"),
            custom_style=settings.get_string("custom-style"),
        )

    @staticmethod
    def new_from_dict(dictionary: dict):
        return FigureSettings(**dictionary)

    def to_dict(self):
        return {key: self.get_property(key) for key in dir(self.props)}

    def get_limits(self) -> list:
        return [self.get_property(key) for key in misc.LIMITS]

    def set_limits(self, limits: list):
        for count, value in enumerate(limits):
            self.set_property(misc.LIMITS[count], value)


_DIRECTIONS = ["bottom", "left", "top", "right"]


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/figure_settings.ui")
class FigureSettingsWindow(Adw.PreferencesWindow):
    __gtype_name__ = "FigureSettingsWindow"

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

    figure_settings = GObject.Property(type=FigureSettings)

    def __init__(self, application, highlighted=None):
        super().__init__(
            application=application, transient_for=application.main_window,
            figure_settings=application.props.figure_settings,
        )

        ignorelist = ["custom_style", "min_selected", "max_selected"]
        for direction in _DIRECTIONS:
            ignorelist.append(f"min_{direction}")
            ignorelist.append(f"max_{direction}")

        ui.bind_values_to_object(
            self.props.figure_settings, self, ignorelist=ignorelist,
        )
        styles_ = sorted(styles.get_user_styles(application).keys())
        self.custom_style.set_model(Gtk.StringList.new(styles_))
        self.custom_style.set_selected(
            styles_.index(self.props.figure_settings.props.custom_style),
        )

        self.set_axes_entries()
        self.no_data_message.set_visible(
            self.props.application.props.data.is_empty(),
        )
        if highlighted is not None:
            getattr(self, highlighted).grab_focus()
        self.present()

    def set_axes_entries(self):
        used_axes = [[direction, False] for direction in _DIRECTIONS]
        for item in self.props.application.props.data:
            for index in item.xposition * 2, 1 + item.yposition * 2:
                used_axes[index][1] = True
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
        self.props.application.props.view_clipboard.add()
        self.destroy()

    @Gtk.Template.Callback()
    def on_custom_style_select(self, comborow, _ignored):
        selected_style = comborow.get_selected_item().get_string()
        if selected_style != self.props.figure_settings.props.custom_style:
            self.props.figure_settings.props.custom_style = selected_style
