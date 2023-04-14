# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk
from matplotlib import pyplot

from graphs import graphs, plot_styles, plotting_tools, ui, utilities
from graphs.canvas import Canvas

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

    def __init__(self, parent):
        super().__init__()
        self.plot_title.set_text(parent.plot_settings.title)
        self.min_left.set_text(str(min(parent.canvas.axis.get_ylim())))
        self.max_left.set_text(str(max(parent.canvas.axis.get_ylim())))
        self.min_bottom.set_text(str(min(parent.canvas.axis.get_xlim())))
        self.max_bottom.set_text(str(max(parent.canvas.axis.get_xlim())))
        self.min_right.set_text(str(min(parent.canvas.right_axis.get_ylim())))
        self.max_right.set_text(str(max(parent.canvas.right_axis.get_ylim())))
        self.min_top.set_text(str(min(parent.canvas.top_left_axis.get_xlim())))
        self.max_top.set_text(str(max(parent.canvas.top_left_axis.get_xlim())))

        self.plot_x_label.set_text(parent.plot_settings.xlabel)
        self.plot_y_label.set_text(parent.plot_settings.ylabel)
        self.plot_top_label.set_text(parent.plot_settings.top_label)
        self.plot_right_label.set_text(parent.plot_settings.right_label)
        utilities.set_chooser(
            self.plot_x_scale, parent.plot_settings.xscale)
        utilities.set_chooser(
            self.plot_y_scale, parent.plot_settings.yscale)
        utilities.set_chooser(
            self.plot_top_scale, parent.plot_settings.top_scale)
        utilities.set_chooser(
            self.plot_right_scale, parent.plot_settings.right_scale)
        self.use_custom_plot_style.set_enable_expansion(
            parent.plot_settings.use_custom_plot_style)
        utilities.populate_chooser(
            self.custom_plot_style, plot_styles.get_user_styles(parent).keys())
        utilities.set_chooser(
            self.custom_plot_style, parent.plot_settings.custom_plot_style)
        self.plot_legend.set_enable_expansion(
            parent.plot_settings.legend)
        utilities.set_chooser(
            self.plot_legend_position,
            parent.plot_settings.legend_position.capitalize())
        self.hide_unused_axes_limits(parent)
        if len(parent.datadict) > 0:
            self.no_data_message.set_visible(False)
        self.connect("close-request", self.on_close, parent)
        self.set_transient_for(parent.main_window)
        self.present()


    def hide_unused_axes_limits(self, parent):
        used_axes = utilities.get_used_axes(parent)[0]
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

    def set_limits(self, parent):
        min_left = float(self.min_left.get_text())
        max_left = float(self.max_left.get_text())
        min_bottom = float(self.min_bottom.get_text())
        max_bottom = float(self.max_bottom.get_text())
        min_right = float(self.min_right.get_text())
        max_right = float(self.max_right.get_text())
        min_top = float(self.min_top.get_text())
        max_top = float(self.max_top.get_text())

        parent.canvas.axis.set_xlim(min_bottom, max_bottom)
        parent.canvas.axis.set_ylim(min_left, max_left)
        parent.canvas.right_axis.set_ylim(min_right, max_right)
        parent.canvas.top_left_axis.set_xlim(min_top, max_top)

    def on_close(self, _, parent):
        plot_settings = parent.plot_settings
        # Check if style is changed
        if plot_settings.use_custom_plot_style != \
                self.use_custom_plot_style.get_enable_expansion():
            self.style_changed = True
        elif plot_settings.custom_plot_style != \
                self.custom_plot_style.get_selected_item().get_string():
            self.style_changed = True
        else:
            self.style_changed = False

        # Set new plot settings
        plot_settings.title = self.plot_title.get_text()
        plot_settings.xlabel = self.plot_x_label.get_text()
        plot_settings.ylabel = self.plot_y_label.get_text()
        plot_settings.top_label = self.plot_top_label.get_text()
        plot_settings.right_label = self.plot_right_label.get_text()
        plot_settings.xscale = \
            self.plot_x_scale.get_selected_item().get_string()
        plot_settings.yscale = \
            self.plot_y_scale.get_selected_item().get_string()
        plot_settings.top_scale = \
            self.plot_top_scale.get_selected_item().get_string()
        plot_settings.right_scale = \
            self.plot_right_scale.get_selected_item().get_string()
        plot_settings.legend = self.plot_legend.get_enable_expansion()
        plot_settings.legend_position = \
            self.plot_legend_position.get_selected_item().get_string().lower()
        plot_settings.use_custom_plot_style = \
            self.use_custom_plot_style.get_enable_expansion()
        plot_settings.custom_plot_style = \
            self.custom_plot_style.get_selected_item().get_string()

        # Set color cycle
        if parent.preferences.config["override_style_change"]:
            parent.canvas = Canvas(parent=parent)
            if self.style_changed:
                for item in parent.datadict.values():
                    item.color = None
                    item.color = plotting_tools.get_next_color(parent)
                    item.linestyle = pyplot.rcParams["lines.linestyle"]
                    item.linewidth = float(pyplot.rcParams["lines.linewidth"])
                    item.markerstyle = pyplot.rcParams["lines.marker"]
                    item.markersize = \
                        float(pyplot.rcParams["lines.markersize"])

        # Reload UI
        ui.reload_item_menu(parent)
        graphs.reload(parent)
        self.set_limits(parent)
