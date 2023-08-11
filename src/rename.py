# SPDX-License-Identifier: GPL-3.0-or-later
from gettext import gettext as _

from gi.repository import Adw, Gtk

from graphs import graphs


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/rename_window.ui")
class RenameWindow(Adw.Window):
    __gtype_name__ = "RenameWindow"
    text_entry = Gtk.Template.Child()
    preferencegroup = Gtk.Template.Child()

    def __init__(self, application, item):
        super().__init__(application=application,
                         transient_for=application.main_window)
        self.item = item
        title = _("Rename Label")
        label = _("Label")
        text = self.item.get_text()
        if self.item == self.props.application.canvas.title:
            title = _("Rename Title")
            label = _("Title")
            text = self.props.application.plot_settings.title
        self.set_title(title)
        self.text_entry.set_title(label)
        self.text_entry.set_text(text)
        self.present()

    @Gtk.Template.Callback()
    def on_accept(self, _widget):
        text = self.text_entry.get_text()
        if self.item == self.props.application.canvas.top_label:
            self.props.application.plot_settings.top_label = text
        if self.item == self.props.application.canvas.left_label:
            self.props.application.plot_settings.left_label = text
        if self.item == self.props.application.canvas.bottom_label:
            self.props.application.plot_settings.bottom_label = text
        if self.item == self.props.application.canvas.right_label:
            self.props.application.plot_settings.right_label = text
        if self.item == self.props.application.canvas.title:
            self.props.application.plot_settings.title = text
        graphs.refresh(self.props.application)
        self.destroy()
