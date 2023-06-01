# SPDX-License-Identifier: GPL-3.0-or-later
from gettext import gettext as _

from gi.repository import Adw, Gtk

from graphs import graphs


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/rename_window.ui")
class RenameWindow(Adw.Window):
    __gtype_name__ = "RenameWindow"
    confirm_button = Gtk.Template.Child()
    text_entry = Gtk.Template.Child()
    preferencegroup = Gtk.Template.Child()

    def __init__(self, parent, item):
        super().__init__()
        title = _("Rename Label")
        group_title = _("Change Label")
        group_description = \
            _("Here you can change the label of the selected axis.")
        text = item.get_text()
        if item == parent.canvas.title:
            title = _("Rename Title")
            group_title = _("Change Title")
            group_description = \
                _("Here you can change the title of the plot.")
            text = parent.plot_settings.title
        self.set_title(title)
        self.preferencegroup.set_title(group_title)
        self.preferencegroup.set_description(group_description)
        self.text_entry.set_text(text)
        self.set_transient_for(parent.main_window)
        self.confirm_button.connect("clicked", self.on_accept, parent, item)
        self.present()

    def on_accept(self, _widget, parent, item):
        text = self.text_entry.get_text()
        if item == parent.canvas.top_label:
            parent.plot_settings.top_label = text
        if item == parent.canvas.left_label:
            parent.plot_settings.ylabel = text
        if item == parent.canvas.bottom_label:
            parent.plot_settings.xlabel = text
        if item == parent.canvas.right_label:
            parent.plot_settings.right_label = text
        if item == parent.canvas.title:
            parent.plot_settings.title = text
        graphs.reload(parent)
        self.destroy()
