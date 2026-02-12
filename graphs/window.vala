// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gdk;
using Gtk;

namespace Graphs {
    /**
     * Main window
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/window.ui")]
    public class Window : Adw.ApplicationWindow {

        [GtkChild]
        private unowned Button view_back_button { get; }

        [GtkChild]
        private unowned Button view_forward_button { get; }

        [GtkChild]
        private unowned Button optimize_limits_button { get; }

        [GtkChild]
        public unowned Adw.OverlaySplitView overlay_split_view { get; }

        [GtkChild]
        private unowned Adw.ToastOverlay toast_overlay { get; }

        [GtkChild]
        private unowned Adw.WindowTitle content_title { get; }

        [GtkChild]
        private unowned Overlay drag_overlay { get; }

        [GtkChild]
        private unowned Revealer drag_revealer { get; }

        [GtkChild]
        protected unowned Adw.ToolbarView content_view { get; }

        [GtkChild]
        private unowned Adw.NavigationView sidebar_navigation_view { get; }

        [GtkChild]
        private unowned MainSidebarPage main_page { get; }

        [GtkChild]
        private unowned EditItemPage edit_page { get; }


        public Data data { get; construct set; }
        protected CssProvider css_provider { get; private set; }
        protected EventControllerKey key_controller { get; private set; }

        public int mode {
            get { return main_page.mode; }
            set { main_page.mode = value; }
        }

        public Canvas canvas {
            get { return toast_overlay.get_child () as Canvas; }
            set {
                value.bind_property ("mode", this, "mode", 2);
                toast_overlay.set_child (value);
                value.grab_focus ();
            }
        }

        public Operations operations {
            get { return main_page.operations; }
            set { main_page.operations = value; }
        }

        public bool is_main_view {
            get { return sidebar_navigation_view.get_visible_page () == main_page; }
        }

        private bool _force_close = false;
        private uint _inhibit_cookie = 0;
        private FigureSettingsPage figure_settings_page;

        construct {
            this.css_provider = new CssProvider ();
            StyleContext.add_provider_for_display (
                Display.get_default (), css_provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );

            this.key_controller = new EventControllerKey ();
            ((Widget) this).add_controller (key_controller);

            var item_drop_target = new Gtk.DropTarget (typeof (ItemBox), Gdk.DragAction.MOVE);
            item_drop_target.drop.connect ((drop, val, x, y) => {
                var value_row = val.get_object () as ItemBox?;
                var target_row = main_page.item_list.get_row_at_y ((int) y) as ItemBox?;
                // If value or the target row is null, do not accept the drop
                if (value_row == null || target_row == null) return false;

                // Reject if the value row is not from this instance
                if (value_row.window != this) return false;

                target_row.change_position (value_row.get_index ());
                target_row.set_state_flags (Gtk.StateFlags.NORMAL, true);

                return true;
            });
            main_page.item_list.add_controller (item_drop_target);

            var file_drop_target = new Gtk.DropTarget (typeof (Gdk.FileList), Gdk.DragAction.COPY);
            file_drop_target.notify["current-drop"].connect (() => {
                bool reveal = file_drop_target.current_drop != null;
                drag_revealer.reveal_child = reveal;
                if (reveal) {
                    drag_overlay.child.add_css_class ("blurred");
                } else {
                    drag_overlay.child.remove_css_class ("blurred");
                }
            });
            file_drop_target.drop.connect ((drop, val, x, y) => {
                var file_list = ((Gdk.FileList) val).get_files ();
                var settings_list = new GLib.ListStore (typeof (ImportSettings));
                foreach (File file in file_list) {
                    settings_list.append (DataImporter.get_settings_for_file (file));
                }
                new ImportDialog (this, settings_list);
                return true;
            });
            drag_overlay.add_controller (file_drop_target);

            sidebar_navigation_view.pushed.connect (() => {
                notify_property ("is_main_view");
                update_history_actions ();
                update_close_project_action ();
            });
            sidebar_navigation_view.popped.connect ((view, page) => {
                if (is_main_view) data.add_history_state ();
                notify_property ("is_main_view");
                update_history_actions ();
                update_close_project_action ();
            });

#if DEBUG
            add_css_class ("devel");
            main_page.set_title (_("Graphs (Development)"));
#endif
        }

        protected void setup () {
            var application = application as Application;

            content_view.set_name ("view" + application.get_next_css_counter ().to_string ());

            Actions.setup_local (this);

            this.operations = new Operations (this);

            data.notify["can-undo"].connect (update_history_actions);
            data.notify["can-redo"].connect (update_history_actions);
            update_history_actions ();
            update_close_project_action ();

            data.bind_property ("can_view_back", view_back_button, "sensitive", 2);
            data.bind_property ("can_view_forward", view_forward_button, "sensitive", 2);

            data.items_changed.connect (on_items_changed);
            data.selection_changed.connect (on_selection_changed);
            data.notify["unsaved"].connect (on_unsaved_change);

            on_items_changed ();
            on_unsaved_change ();
        }

        private void update_history_actions () {
            bool enable = is_main_view;
            var undo_action = lookup_action ("undo") as SimpleAction;
            var redo_action = lookup_action ("redo") as SimpleAction;
            undo_action.set_enabled (enable && data.can_undo);
            redo_action.set_enabled (enable && data.can_redo);
        }

        private void update_close_project_action () {
            var close_action = lookup_action ("close-project") as SimpleAction;
            close_action.set_enabled (data.file != null && is_main_view);
        }

        /**
         * Inhibit session end when there is unsaved data present.
         * Disable save actions if there is no unsaved data.
         * Update window title.
         */
        private void on_unsaved_change () {
            update_close_project_action ();
            string title;
            string path;
            if (data.file == null) {
                title = _("Untitled Project");
                path = _("Draft");
            } else {
                title = Tools.get_filename (data.file);
                path = Tools.get_friendly_path (data.file);
            }
            // Translators: Window title that will be formatted with the project name.
            set_title (_("Graphs — %s").printf (title));
            content_title.set_subtitle (path);

            var save_action = lookup_action ("save-project") as SimpleAction;
            var save_as_action = lookup_action ("save-project-as") as SimpleAction;
            if (data.unsaved) {
                if (_inhibit_cookie == 0) _inhibit_cookie = application.inhibit (
                    this,
                    ApplicationInhibitFlags.LOGOUT,
                    title
                );
                save_action.set_enabled (true);
                save_as_action.set_enabled (true);
                content_title.set_title ("• " + title);
            } else {
                if (_inhibit_cookie > 0) {
                    application.uninhibit (_inhibit_cookie);
                    _inhibit_cookie = 0;
                }
                save_action.set_enabled (false);
                save_as_action.set_enabled (data.file != null);
                content_title.set_title (title);
            }
        }

        private void on_items_changed () {
            main_page.item_list.remove_all ();
            var export_data_action = lookup_action ("export-data") as SimpleAction;
            var optimize_limits_action = lookup_action ("optimize-limits") as SimpleAction;
            if (data.is_empty ()) {
                main_page.set_show_empty_data_page (true);
                operations.shift_button.set_sensitive (false);
                operations.smoothen_button.set_sensitive (false);
                operations.set_cut_sensitivity (false);
                operations.set_entry_sensitivity (false);
                export_data_action.set_enabled (false);
                optimize_limits_action.set_enabled (false);
                return;
            }
            main_page.set_show_empty_data_page (false);
            bool items_selected = false;
            bool data_items_selected = false;
            uint index = 0;
            foreach (Item item in data) {
                string typename = item.get_type ().name ();
                bool data_item = typename == "GraphsDataItem" || typename == "GraphsGeneratedDataItem";
                append_item_row (item, index, data_item);

                items_selected = items_selected || item.selected;
                data_items_selected = data_items_selected || (item.selected && data_item);
                index++;
            }
            operations.shift_button.set_sensitive (items_selected);
            operations.smoothen_button.set_sensitive (data_items_selected);
            operations.set_cut_sensitivity (data_items_selected && mode == 2);
            operations.set_entry_sensitivity (items_selected);
            export_data_action.set_enabled (items_selected);
            optimize_limits_action.set_enabled (true);
        }

        public void on_selection_changed () {
            var export_data_action = lookup_action ("export-data") as SimpleAction;
            if (data.is_empty ()) {
                operations.shift_button.set_sensitive (false);
                operations.smoothen_button.set_sensitive (false);
                operations.set_cut_sensitivity (false);
                operations.set_entry_sensitivity (false);
                export_data_action.set_enabled (false);
                return;
            }
            bool items_selected = false;
            bool data_items_selected = false;
            foreach (Item item in data) {
                string typename = item.get_type ().name ();
                bool data_item = typename == "GraphsDataItem" || typename == "GraphsGeneratedDataItem";

                items_selected = items_selected || item.selected;
                data_items_selected = data_items_selected || (item.selected && data_item);
                if (items_selected && data_items_selected) break;
            }
            operations.shift_button.set_sensitive (items_selected);
            operations.smoothen_button.set_sensitive (data_items_selected);
            operations.set_cut_sensitivity (data_items_selected && mode == 2);
            operations.set_entry_sensitivity (items_selected);
            export_data_action.set_enabled (items_selected);
        }

        private void append_item_row (Item item, uint index, bool is_data_item) {
            var row = new ItemBox (this, item, index);
            row.setup_interactions (is_data_item);

            double drag_x = 0.0;
            double drag_y = 0.0;

            var drop_controller = new Gtk.DropControllerMotion ();
            var drag_source = new Gtk.DragSource () {
                actions = Gdk.DragAction.MOVE
            };

            row.add_controller (drag_source);
            row.add_controller (drop_controller);

            // Drag handling
            drag_source.prepare.connect ((x, y) => {
                drag_x = x;
                drag_y = y;

                Value val = Value (typeof (ItemBox));
                val.set_object (row);

                return new Gdk.ContentProvider.for_value (val);
            });

            drag_source.drag_begin.connect ((drag) => {
                var drag_widget = new Gtk.ListBox ();
                drag_widget.set_size_request (row.get_width (), row.get_height ());
                drag_widget.add_css_class ("boxed-list");

                var drag_row = new ItemBox (this, item, index);

                drag_widget.append (drag_row);
                drag_widget.drag_highlight_row (drag_row);

                var icon = Gtk.DragIcon.get_for_drag (drag) as Gtk.DragIcon;
                icon.child = drag_widget;

                drag.set_hotspot ((int) drag_x, (int) drag_y);
            });

            // Update row visuals during DnD operation
            drop_controller.enter.connect (() => main_page.item_list.drag_highlight_row (row));
            drop_controller.leave.connect (() => main_page.item_list.drag_unhighlight_row ());

            row.activated.connect (() => {
                edit_item (item);
            });

            main_page.item_list.append (row);
        }

        public void push_sidebar_page (Adw.NavigationPage page) {
            sidebar_navigation_view.push (page);
        }

        public void edit_item (Item item) {
            edit_page.clear ();
            edit_page.append (new EditItemBaseBox (item));

            PythonHelper.create_item_settings (edit_page, item);

            push_sidebar_page (edit_page);
        }

        public void open_figure_settings (string? highlighted = null) {
            if (is_main_view) {
                figure_settings_page = new FigureSettingsPage (this);
                push_sidebar_page (figure_settings_page);
            }

            if (highlighted != null && sidebar_navigation_view.get_visible_page () == figure_settings_page) {
                figure_settings_page.focus_widget (highlighted);
            }
        }

        /**
         * Add a toast to the window.
         */
        public void add_toast (Adw.Toast toast) {
            toast_overlay.add_toast (toast);
        }

        /**
         * Add a toast to the window.
         *
         * The toast is created automatically with the given title.
         */
        public void add_toast_string (string title) {
            add_toast (new Adw.Toast (title));
        }

        /**
         * Add a toast to the window.
         *
         * The toast is created automatically with the given title.
         * An action is automatically created, to open the containing folder
         * of file.
         */
        public void add_toast_string_with_file (string title, File file) {
            SimpleAction action = new SimpleAction ("open-file-location", null);
            action.activate.connect (() => {
                Tools.open_file_location (file);
            });
            add_action (action);
            add_toast (new Adw.Toast (title) {
                button_label = _("Open Location"),
                action_name = "win.open-file-location"
            });
        }

        /**
         * Add Toast with undo action.
         */
        public void add_undo_toast (string title) {
            add_toast (new Adw.Toast (title) {
                button_label = _("Undo"),
                action_name = "win.undo"
            });
        }

        public override bool close_request () {
            var application = application as Application;

            if (_force_close) {
                application.on_main_window_closed (this);
                return false;
            }

            if (data.unsaved) {
                var dialog = Tools.build_dialog ("save_project_changes") as Adw.AlertDialog;
                dialog.response.connect ((d, response) => {
                    switch (response) {
                        case "discard": {
                            _force_close = true;
                            close ();
                            break;
                        }
                        case "save": {
                            Project.save.begin (this, false, (o, result) => {
                                if (Project.save.end (result)) {
                                    _force_close = true;
                                    close ();
                                }
                            });
                            break;
                        }
                    }
                });
                dialog.present (this);
                return true;
            }
            application.on_main_window_closed (this);
            return false;
        }
    }
}
