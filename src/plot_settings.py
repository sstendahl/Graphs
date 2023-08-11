# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, GObject, Gtk

from graphs import graphs, misc, plot_styles, plotting_tools, ui, utilities
from graphs.item import Item

from matplotlib import pyplot


class FigureSettings(GObject.Object):
    __gtype_name__ = "FigureSettings"

    title = GObject.Property(type=str, default="")
    bottom_label = GObject.Property(type=str, default="")
    left_label = GObject.Property(type=str, default="")
    top_label = GObject.Property(type=str, default="")
    right_label = GObject.Property(type=str, default="")

    bottom_scale = GObject.Property(type=str, default="linear")
    left_scale = GObject.Property(type=str, default="linear")
    top_scale = GObject.Property(type=str, default="linear")
    right_scale = GObject.Property(type=str, default="linear")

    legend = GObject.Property(type=bool, default=True)
    legend_position = GObject.Property(type=str, default="Best")
    use_custom_style = GObject.Property(type=bool, default=False)
    custom_style = GObject.Property(type=str, default="adwaita")

    min_bottom = GObject.Property(type=int, default=0)
    max_bottom = GObject.Property(type=int, default=1)
    min_left = GObject.Property(type=int, default=0)
    max_left = GObject.Property(type=int, default=10)
    min_top = GObject.Property(type=int, default=0)
    max_top = GObject.Property(type=int, default=1)
    min_right = GObject.Property(type=int, default=0)
    max_right = GObject.Property(type=int, default=10)

    @staticmethod
    def new(settings):
        def _get_scale(scale):
            return "linear" if settings.get_enum(scale) == 0 else "log"

        return FigureSettings(
            bottom_scale=_get_scale("bottom-scale"),
            left_scale=_get_scale("left-scale"),
            right_scale=_get_scale("right-scale"),
            top_scale=_get_scale("top-scale"),
            title=settings.get_string("title"),
            legend=settings.get_boolean("legend"),
            use_custom_style=settings.get_boolean("use-custom-style"),
            legend_position=settings.get_string("legend-position"),
            custom_style=settings.get_string("custom-style"),
        )

    @staticmethod
    def new_from_dict(dictionary: dict):
        return FigureSettings(**dictionary)

    def to_dict(self):
        return {key: self.get_property(key) for key in dir(self.props)}


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/plot_settings.ui")
class PlotSettingsWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PlotSettingsWindow"
    plot_title = Gtk.Template.Child()
    plot_x_label = Gtk.Template.Child()
    plot_y_label = Gtk.Template.Child()
    plot_top_label = Gtk.Template.Child()
    plot_right_label = Gtk.Template.Child()
    plot_x_scale = Gtk.Template.Child()
    plot_y_scale = Gtk.Template.Child()
    plot_top_scale = Gtk.Template.Child()
    plot_right_scale = Gtk.Template.Child()
    plot_legend = Gtk.Template.Child()
    plot_legend_position = Gtk.Template.Child()
    use_custom_plot_style = Gtk.Template.Child()
    custom_plot_style = Gtk.Template.Child()
    min_left = Gtk.Template.Child()
    max_left = Gtk.Template.Child()
    min_bottom = Gtk.Template.Child()
    max_bottom = Gtk.Template.Child()
    min_right = Gtk.Template.Child()
    max_right = Gtk.Template.Child()
    min_top = Gtk.Template.Child()
    max_top = Gtk.Template.Child()
    no_data_message = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application,
                         transient_for=application.main_window)
        self.plot_settings = self.props.application.plot_settings

        if self.plot_settings.title is not None:
            self.plot_title.set_text(self.plot_settings.title)
        self.min_left.set_text(str(self.plot_settings.min_left))
        self.max_left.set_text(str(self.plot_settings.max_left))
        self.min_bottom.set_text(str(self.plot_settings.min_bottom))
        self.max_bottom.set_text(str(self.plot_settings.max_bottom))
        self.min_right.set_text(str(self.plot_settings.min_right))
        self.max_right.set_text(str(self.plot_settings.max_right))
        self.min_top.set_text(str(self.plot_settings.min_top))
        self.max_top.set_text(str(self.plot_settings.max_top))

        if self.plot_settings.bottom_label != "":
            self.plot_x_label.set_text(self.plot_settings.bottom_label)
        if self.plot_settings.left_label != "":
            self.plot_y_label.set_text(self.plot_settings.left_label)
        if self.plot_settings.top_label != "":
            self.plot_top_label.set_text(self.plot_settings.top_label)
        if self.plot_settings.right_label != "":
            self.plot_right_label.set_text(self.plot_settings.right_label)
        utilities.populate_chooser(self.plot_x_scale, misc.SCALES)
        utilities.set_chooser(
            self.plot_x_scale, self.plot_settings.bottom_scale)
        utilities.populate_chooser(self.plot_y_scale, misc.SCALES)
        utilities.set_chooser(self.plot_y_scale, self.plot_settings.left_scale)
        utilities.populate_chooser(self.plot_top_scale, misc.SCALES)
        utilities.set_chooser(
            self.plot_top_scale, self.plot_settings.top_scale)
        utilities.populate_chooser(self.plot_right_scale, misc.SCALES)
        utilities.set_chooser(
            self.plot_right_scale, self.plot_settings.right_scale)
        self.use_custom_plot_style.set_enable_expansion(
            self.plot_settings.use_custom_style)
        utilities.populate_chooser(
            self.custom_plot_style,
            sorted(plot_styles.get_user_styles(self.props.application).keys()),
            translate=False)
        utilities.set_chooser(
            self.custom_plot_style, self.plot_settings.custom_style)
        self.plot_legend.set_enable_expansion(self.plot_settings.legend)
        utilities.populate_chooser(
            self.plot_legend_position, misc.LEGEND_POSITIONS)
        utilities.set_chooser(
            self.plot_legend_position,
            self.plot_settings.legend_position)
        self.hide_unused_axes_limits()
        if len(self.props.application.datadict) > 0:
            self.no_data_message.set_visible(False)
        self.present()

    def hide_unused_axes_limits(self):
        used_axes = utilities.get_used_axes(self.props.application)[0]
        if not used_axes["left"]:
            self.min_left.set_visible(False)
            self.max_left.set_visible(False)
        if not used_axes["right"]:
            self.min_right.set_visible(False)
            self.max_right.set_visible(False)
        if not used_axes["top"]:
            self.min_top.set_visible(False)
            self.max_top.set_visible(False)
        if not used_axes["bottom"]:
            self.min_bottom.set_visible(False)
            self.max_bottom.set_visible(False)

    @Gtk.Template.Callback()
    def on_close(self, *_args):
        # Set new plot settings
        if self.plot_title.get_text() != "":
            self.plot_settings.title = self.plot_title.get_text()
        if self.plot_x_label.get_text() != "":
            self.plot_settings.bottom_label = self.plot_x_label.get_text()
        if self.plot_y_label.get_text() != "":
            self.plot_settings.left_label = self.plot_y_label.get_text()
        if self.plot_top_label.get_text() != "":
            self.plot_settings.top_label = self.plot_top_label.get_text()
        if self.plot_right_label.get_text() != "":
            self.plot_settings.right_label = self.plot_right_label.get_text()
        self.plot_settings.bottom_scale = \
            utilities.get_selected_chooser_item(self.plot_x_scale)
        self.plot_settings.yscale = \
            utilities.get_selected_chooser_item(self.plot_y_scale)
        self.plot_settings.top_scale = \
            utilities.get_selected_chooser_item(self.plot_top_scale)
        self.plot_settings.right_scale = \
            utilities.get_selected_chooser_item(self.plot_right_scale)
        self.plot_settings.legend = self.plot_legend.get_enable_expansion()
        self.plot_settings.legend_position = \
            utilities.get_selected_chooser_item(self.plot_legend_position)

        def get_float(entry):
            return utilities.string_to_float(entry.get_text())

        self.props.application.canvas.limits = {
            "min_bottom": get_float(self.min_bottom),
            "max_bottom": get_float(self.max_bottom),
            "min_top": get_float(self.min_top),
            "max_top": get_float(self.max_top),
            "min_left": get_float(self.min_left),
            "max_left": get_float(self.max_left),
            "min_right": get_float(self.min_right),
            "max_right": get_float(self.max_right),
        }

        graphs.refresh(self.props.application)
        self.props.application.props.clipboard.add()
        self.props.application.props.view_clipboard.add()

    @Gtk.Template.Callback()
    def on_custom_style_select(self, comborow, _ignored):
        selected_style = utilities.get_selected_chooser_item(comborow)
        if selected_style == self.plot_settings.custom_style:
            return
        self.plot_settings.custom_style = selected_style
        self._handle_style_change()

    @Gtk.Template.Callback()
    def on_custom_style_enable(self, expanderrow, _ignored):
        use_custom_style = expanderrow.get_enable_expansion()
        if use_custom_style == self.plot_settings.use_custom_style:
            return
        self.plot_settings.use_custom_style = use_custom_style
        self._handle_style_change()

    def _handle_style_change(self):
        graphs.reload(self.props.application)
        if not self.props.application.get_settings(
                "general").get_boolean("override-item-properties"):
            return
        for item in self.props.application.datadict.values():
            item.color = None
        for item in self.props.application.datadict.values():
            item.color = plotting_tools.get_next_color(self.props.application)
            if isinstance(item, Item):
                item.linestyle = pyplot.rcParams["lines.linestyle"]
                item.linewidth = float(pyplot.rcParams["lines.linewidth"])
                item.markerstyle = pyplot.rcParams["lines.marker"]
                item.markersize = float(pyplot.rcParams["lines.markersize"])
        graphs.refresh(self.props.application)
        ui.reload_item_menu(self.props.application)
