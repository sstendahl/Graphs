# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk

from graphs import graphs, utilities, plot_styles


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
    plot_legend_check = Gtk.Template.Child()
    plot_style = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()

        self.plot_title.set_text(parent.plot_settings.title)
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
        utilities.populate_chooser(
            self.plot_style, plot_styles.get_user_styles(parent).keys())
        utilities.set_chooser(self.plot_style, parent.plot_settings.plot_style)
        self.plot_legend_check.set_active(parent.plot_settings.legend)

        self.connect("close-request", self.on_close, parent)
        self.set_transient_for(parent.main_window)
        self.present()

    def on_close(self, _, parent):
        plot_settings = parent.plot_settings
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
        plot_settings.legend = self.plot_legend_check.get_active()
        plot_settings.plot_style = \
            self.plot_style.get_selected_item().get_string()
        graphs.reload(parent)
