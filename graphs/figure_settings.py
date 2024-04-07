# SPDX-License-Identifier: GPL-3.0-or-later
"""Figure Settings Dialog."""
import contextlib
from gettext import gettext as _

from gi.repository import Adw, GObject, Graphs, Gtk

from graphs import misc, styles, ui, utilities


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/figure_settings.ui")
class FigureSettingsDialog(Adw.Dialog):
    """Figure Settings Dialog."""

    __gtype_name__ = "GraphsFigureSettingsDialog"

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
    application = GObject.Property(type=Graphs.Application)

    def __init__(
        self,
        application: Graphs.Application,
        highlighted: str = None,
    ):
        """Initialize the Figure Settings window and set the widget entries."""
        figure_settings = application.get_data().get_figure_settings()
        super().__init__(
            application=application,
            figure_settings=figure_settings,
        )

        ignorelist = ["custom_style", "use_custom_style"]
        for prop in ignorelist:
            figure_settings.connect(
                "notify::" + prop.replace("_", "-"),
                self._update_stylename,
            )
        for direction in misc.DIRECTIONS + ["selected"]:
            ignorelist.append(f"min_{direction}")
            ignorelist.append(f"max_{direction}")

        ui.bind_values_to_object(figure_settings, self, ignorelist=ignorelist)
        self.set_axes_entries()
        if highlighted is not None:
            getattr(self, highlighted).grab_focus()
        self.style_editor = styles.StyleEditor(self)
        preview_handler = Graphs.PreviewWidgetHandler()
        preview_handler.connect("edit-request", self.edit_style)
        self.grid_view.set_factory(preview_handler.get_factory())
        self.grid_view.set_model(
            application.get_figure_style_manager().get_selection_model(),
        )
        self._update_stylename()
        self.present(application.get_window())

    def _update_stylename(self, *_args):
        style_manager = self.props.application.get_figure_style_manager()
        self.style_name.set_text(style_manager.get_selected_stylename())

    def set_axes_entries(self) -> None:
        """
        Handle axis entries.

        Set the labels and visibility of all entries that are related to the
        axes: scale, limits and label. Whenever two opposite axes are used
        simultaniously, the title of the entry will get a directional prefix.
        """
        visible_axes = self.props.application.get_data().get_used_positions()
        # Get the label for each direction, use directional prefix if
        # two opposite X/Y axes are used simultaniously.
        labels = {
            "top": {
                "min":
                _("Top X Axis Minimum") if visible_axes[0] and visible_axes[1]
                else _("X Axis Minimum"),
                "max":
                _("Top X Axis Maximum") if visible_axes[0] and visible_axes[1]
                else _("X Axis Maximum"),
                "scale":
                _("Top X Axis Scale")
                if visible_axes[0] and visible_axes[1] else _("X Axis Scale"),
                "label":
                _("Top X Axis Label")
                if visible_axes[0] and visible_axes[1] else _("X Axis Label"),
            },
            "bottom": {
                "min":
                _("Bottom X Axis Minimum") if visible_axes[0]
                and visible_axes[1] else _("X Axis Minimum"),
                "max":
                _("Bottom X Axis Maximum") if visible_axes[0]
                and visible_axes[1] else _("X Axis Maximum"),
                "scale":
                _("Bottom X Axis Scale")
                if visible_axes[0] and visible_axes[1] else _("X Axis Scale"),
                "label":
                _("Bottom X Axis Label")
                if visible_axes[0] and visible_axes[1] else _("X Axis Label"),
            },
            "left": {
                "min":
                _("Left Y Axis Minimum") if visible_axes[2] and visible_axes[3]
                else _("Y Axis Minimum"),
                "max":
                _("Left Y Axis Maximum") if visible_axes[2] and visible_axes[3]
                else _("Y Axis Maximum"),
                "scale":
                _("Left Y Axis Scale")
                if visible_axes[2] and visible_axes[3] else _("Y Axis Scale"),
                "label":
                _("Left Y Axis Label")
                if visible_axes[2] and visible_axes[3] else _("Y Axis Label"),
            },
            "right": {
                "min":
                _("Right Y Axis Minimum") if visible_axes[2]
                and visible_axes[3] else _("Y Axis Minimum"),
                "max":
                _("Right Y Axis Maximum") if visible_axes[2]
                and visible_axes[3] else _("Y Axis Maximum"),
                "scale":
                _("Right Y Axis Scale")
                if visible_axes[2] and visible_axes[3] else _("Y Axis Scale"),
                "label":
                _("Right Y Axis Label")
                if visible_axes[2] and visible_axes[3] else _("Y Axis Label"),
            },
        }
        for (direction, visible) in zip(misc.DIRECTIONS, visible_axes):
            if visible:
                for s in ("min_", "max_"):
                    entry = getattr(self, s + direction)
                    entry.set_text(
                        str(
                            self.props.figure_settings.get_property(
                                s + direction,
                            ),
                        ),
                    )
                    entry.connect(
                        "notify::text",
                        self.on_entry_change,
                        s + direction,
                    )

            min_dir = getattr(self, f"min_{direction}")
            min_dir.set_title(labels[direction]["min"])
            max_dir = getattr(self, f"max_{direction}")
            max_dir.set_title(labels[direction]["max"])
            scale = getattr(self, f"{direction}_scale")
            scale.set_title(labels[direction]["scale"])
            label = getattr(self, f"{direction}_label")
            label.set_title(labels[direction]["label"])
            getattr(self, direction + "_limits").set_visible(visible)
            getattr(self, direction + "_scale").set_visible(visible)
            getattr(self, direction + "_label").set_visible(visible)

    def on_entry_change(self, entry, _param, prop) -> None:
        """Bind the entry upon change."""
        with contextlib.suppress(SyntaxError):
            self.props.figure_settings.set_property(
                prop,
                utilities.string_to_float(entry.get_text()),
            )

    def edit_style(self, _handler, style) -> None:
        """Load the style editor for the selected style."""
        self.style_editor.load_style(style)
        self.navigation_view.push(self.style_editor)

    @Gtk.Template.Callback()
    def on_pop(self, _view, page) -> None:
        """
        Handle style editor removal.

        Callback when removing the current stack in the NavigationOverview.
        Saves the changes to the style if the stack was a style editor page.
        """
        if page == self.style_editor:
            self.style_editor.save_style()
            style_manager = self.props.application.get_figure_style_manager()
            style_manager._on_style_change()

    @Gtk.Template.Callback()
    def choose_style(self, _button) -> None:
        """Load the style overview."""
        self.navigation_view.push(self.style_overview)

    @Gtk.Template.Callback()
    def add_style(self, _button) -> None:
        """Open the new style window."""
        style_manager = self.props.application.get_figure_style_manager()

        def on_accept(_dialog, template, name):
            style_manager.copy_style(template, name)

        dialog = Graphs.AddStyleDialog.new(style_manager, self)
        dialog.connect("accept", on_accept)

    @Gtk.Template.Callback()
    def on_close(self, *_args) -> None:
        """
        Handle closing.

        Closes the figure settings, saves the current style and adds the
        new state to the clipboard
        """
        self.style_editor.save_style()
        data = self.props.application.get_data()
        data.add_view_history_state()
        data.add_history_state()

    @Gtk.Template.Callback()
    def on_set_as_default(self, _button) -> None:
        """Set the current figure settings as the new default."""
        figure_settings = self.props.figure_settings
        settings = self.props.application.get_settings_child("figure")
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
