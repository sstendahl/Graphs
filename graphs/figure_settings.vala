// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Figure settings
     */
    public class FigureSettings : Object {

        public string title { get; set; default = ""; }
        public string bottom_label { get; set; default = ""; }
        public string left_label { get; set; default = ""; }
        public string top_label { get; set; default = ""; }
        public string right_label { get; set; default = ""; }

        public int bottom_scale { get; set; default = 0; }
        public int left_scale { get; set; default = 0; }
        public int top_scale { get; set; default = 0; }
        public int right_scale { get; set; default = 0; }

        public bool legend { get; set; default = true; }
        public int legend_position { get; set; default = 0; }
        public bool use_custom_style { get; set; default = false; }
        public string custom_style { get; set; default = "Adwaita"; }
        public bool hide_unselected { get; set; default = false; }

        public double min_bottom { get; set; default = 0; }
        public double max_bottom { get; set; default = 1; }
        public double min_left { get; set; default = 0; }
        public double max_left { get; set; default = 10; }
        public double min_top { get; set; default = 0; }
        public double max_top { get; set; default = 1; }
        public double min_right { get; set; default = 0; }
        public double max_right { get; set; default = 10; }

        public double min_selected { get; set; default = 0; }
        public double max_selected { get; set; default = 0; }

        public FigureSettings (GLib.Settings settings) {
            Object (
                bottom_scale: settings.get_enum ("bottom-scale"),
                left_scale: settings.get_enum ("left-scale"),
                right_scale: settings.get_enum ("right-scale"),
                top_scale: settings.get_enum ("top-scale"),
                title: settings.get_string ("title"),
                bottom_label: settings.get_string ("bottom-label"),
                left_label: settings.get_string ("left-label"),
                top_label: settings.get_string ("top-label"),
                right_label: settings.get_string ("right-label"),
                legend: settings.get_boolean ("legend"),
                use_custom_style: settings.get_boolean ("use-custom-style"),
                legend_position: settings.get_enum ("legend-position"),
                custom_style: settings.get_string ("custom-style")
            );
        }

        public double[] get_limits () {
            double[] limits = {};
            foreach (string limit_name in LIMIT_NAMES) {
                double limit;
                get (limit_name, out limit);
                limits += limit;
            }
            return limits;
        }

        public void set_limits (double[] limits)
        requires (limits.length == 8) {
            for (int i = 0; i < LIMIT_NAMES.length; i++) {
                set (LIMIT_NAMES[i], limits[i]);
            }
        }

        public void set_selection_range (double minimum, double maximum)
        requires (0 <= minimum <= 1)
        requires (0 <= maximum <= 1)
        requires (minimum <= maximum) {
            this.min_selected = minimum;
            this.max_selected = maximum;
        }
    }

    private const string PAGE_RESOURCE = "/se/sjoerd/Graphs/ui/figure-settings-page.ui";

    /**
     * Figure settings dialog
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/figure-settings-dialog.ui")]
    public class FigureSettingsDialog : Adw.Dialog {

        [GtkChild]
        public unowned Adw.NavigationView navigation_view { get; }

        [GtkChild]
        private unowned GridView grid_view { get; }

        [GtkChild]
        private unowned Adw.NavigationPage style_overview { get; }

        [GtkChild]
        private unowned Adw.ToastOverlay toast_overlay { get; }

        public Application application { get; construct set; }
        protected Adw.NavigationPage settings_page { get; private set; }
        protected Adw.NavigationPage style_editor { get; protected set; }
        protected FigureSettings figure_settings {
            get { return this.application.data.figure_settings; }
        }

        protected signal void entry_change (Adw.EntryRow entry, string prop);
        protected signal void set_as_default ();
        protected signal void copy_request (string template, string name);
        public signal void load_style_request (Style style);
        public signal void save_style_request ();

        protected void setup (string? highlighted) {
            FigureSettings figure_settings = this.figure_settings;
            GLib.Settings settings = this.application.get_settings_child ("figure");
            var builder = new Builder.from_resource (PAGE_RESOURCE);
            this.settings_page = (Adw.NavigationPage) builder.get_object ("settings_page");
            this.navigation_view.push (this.settings_page);
            foreach (string key in settings.settings_schema.list_keys ()) {
                if (key[-5:] == "style") continue;
                key = key.replace ("-", "_");
                Object object = builder.get_object (key);
                if (object is Adw.EntryRow) {
                    figure_settings.bind_property (key, object, "text", 1 | 2);
                }
                else if (object is Adw.ComboRow) {
                    figure_settings.bind_property (key, object, "selected", 1 | 2);
                }
                else if (object is Adw.ExpanderRow) {
                    figure_settings.bind_property (key, object, "enable-expansion", 1 | 2);
                }
                else if (object is Adw.SwitchRow) {
                    figure_settings.bind_property (key, object, "active", 1 | 2);
                }
                else assert_not_reached ();
            }

            bool[] visible_axes = this.application.data.get_used_positions ();
            bool both_x = visible_axes[0] && visible_axes[1];
            bool both_y = visible_axes[2] && visible_axes[3];
            string[] min_max = {"min", "max"};
            for (int i = 0; i < 4; i++) {
                string direction = DIRECTION_NAMES[i];
                bool visible = visible_axes[i];
                bool x = i < 2;
                if (visible) {
                    foreach (string s in min_max) {
                        string key = s + "_" + direction;
                        var entry = (Adw.EntryRow) builder.get_object (key);
                        double val;
                        figure_settings.get (key, out val);
                        entry.set_text (val.to_string ());
                        entry.notify["text"].connect (() => {
                            this.entry_change.emit (entry, key);
                        });
                        if (s == "min") {
                            if (x && !both_x) entry.set_title (_("X Axis Minimum"));
                            else if (!x && !both_y) entry.set_title (_("Y Axis Minimum"));
                        } else {
                            if (x && !both_x) entry.set_title (_("X Axis Maximum"));
                            else if (!x && !both_y) entry.set_title (_("Y Axis Maximum"));
                        }
                    }
                    var scale = (Adw.ComboRow) builder.get_object (direction + "_scale");
                    var label = (Adw.EntryRow) builder.get_object (direction + "_label");
                    var limits = (Box) builder.get_object (direction + "_limits");
                    scale.set_visible (true);
                    label.set_visible (true);
                    limits.set_visible (true);
                    if (x && !both_x) {
                        scale.set_title (_("X Axis Scale"));
                        label.set_title (_("X Axis Label"));
                    }
                    else if (!x && !both_y) {
                        scale.set_title (_("Y Axis Scale"));
                        label.set_title (_("X Axis Label"));
                    }
                }
            }
            var style_name = (Label) builder.get_object ("style_name");
            StyleManager style_manager = this.application.figure_style_manager;
            style_manager.bind_property (
                "selected_stylename", style_name, "label", 2
            );

            var factory = new SignalListItemFactory ();
            factory.setup.connect (on_factory_setup);
            factory.bind.connect (on_factory_bind);
            this.grid_view.set_factory (factory);
            this.grid_view.set_model (style_manager.selection_model);

            var style_row = (Adw.ActionRow) builder.get_object ("style_row");
            style_row.activated.connect (() => {
                this.navigation_view.push (this.style_overview);
            });
            var button = (Button) builder.get_object ("set_as_default");
            button.clicked.connect (() => {
                this.set_as_default.emit ();
            });

            present (this.application.window);
            if (highlighted != null) {
                var widget = (Widget) builder.get_object (highlighted);
                widget.grab_focus ();
            }
        }

        protected void add_toast_string () {
            this.toast_overlay.add_toast (new Adw.Toast (_("Defaults Updated")));
        }

        [GtkCallback]
        private void on_pop (Adw.NavigationPage page) {
            if (page == this.style_editor) this.save_style_request.emit ();
        }

        [GtkCallback]
        private void add_style () {
            StyleManager style_manager = this.application.figure_style_manager;
            var dialog = new AddStyleDialog (style_manager, this);
            dialog.accept.connect ((d, template, name) => {
                this.copy_request.emit (template, name);
            });
        }

        private void on_factory_setup (Object object) {
            ListItem item = (ListItem) object;
            item.set_child (new StylePreview ());
        }

        private void on_factory_bind (Object object) {
            ListItem item = (ListItem) object;
            StylePreview preview = (StylePreview) item.get_child ();
            Style style = (Style) item.get_item ();
            preview.style = style;
            if (style.mutable && !preview.edit_button.get_visible ()) {
                preview.edit_button.set_visible (true);
                preview.edit_button.clicked.connect (() => {
                    this.load_style_request.emit (style);
                    this.navigation_view.push (this.style_editor);
                });
            }
        }
    }
}
