// SPDX-License-Identifier: GPL-3.0-or-later
using Gdk;
using Gtk;
using Gee;

namespace Graphs {
    public int style_cmp (Style a, Style b) {
        if (a.file == null) return -1;
        else if (b.file == null) return 1;
        return strcmp (a.name.down (), b.name.down ());
    }

    /**
     * Style manager
     */
    public class StyleManager : Object {
        public Application application { get; construct set; }
        public bool use_custom_style { get; set; default = false; }
        public string custom_style { get; set; default = "Adwaita"; }
        public SingleSelection selection_model { get; set; }
        public File style_dir { get; construct set; }
        public string selected_stylename {
            get { return this.get_selected_style ().name; }
        }

        private GLib.ListStore style_model;
        private Gee.AbstractSet<string> stylenames { get; private set; }

        public signal void style_changed (bool recolor_items);
        protected signal void copy_request (string template, string name);
        protected signal Style style_request (File file);

        construct {
            this.style_model = new GLib.ListStore (typeof (Style));
            this.selection_model = new SingleSelection (style_model);
            this.stylenames = new Gee.HashSet<string> ();
            try {
                File config_dir = Tools.get_config_directory ();
                this.style_dir = config_dir.get_child_for_display_name ("styles");
                if (!style_dir.query_exists ()) {
                    style_dir.make_directory_with_parents ();
                }
            } catch {
                assert_not_reached ();
            }
        }

        protected void setup (string system_style) {
            notify["custom-style"].connect (on_custom_style);
            notify["use-custom-style"].connect (on_use_custom_style);

            CompareDataFunc<Style> cmp = style_cmp;
            try {
                var directory = File.new_for_uri ("resource:///se/sjoerd/Graphs/styles");
                FileEnumerator enumerator = directory.enumerate_children (
                    "standard::*",
                    FileQueryInfoFlags.NONE
                );
                FileInfo info = null;
                while ((info = enumerator.next_file ()) != null) {
                    File file = enumerator.get_child (info);
                    var stream = new DataInputStream (file.read ());
                    stream.read_line_utf8 ();
                    size_t size;
                    string name = stream.read_line_utf8 (out size)[2: (long)size];
                    stylenames.add (name);
                    string preview_name = info.get_name ().replace (".mplstyle", ".png");
                    var preview = Gdk.Texture.from_resource (
                        @"/se/sjoerd/Graphs/$preview_name"
                    );
                    style_model.insert_sorted (
                        new Style (name, file, preview, false),
                        cmp
                    );
                }
                enumerator.close ();
            } catch {
                assert_not_reached ();
            }
            style_model.insert (
                0,
                new Style (
                    _("System"),
                    null,
                    Gdk.Texture.from_resource (
                        @"/se/sjoerd/Graphs/system-style-$system_style.png"
                    ),
                    false
                )
            );
            application.python_helper.run_method (this, "_update_system_style");
            try {
                FileEnumerator enumerator = style_dir.enumerate_children (
                    "standard::*",
                    FileQueryInfoFlags.NONE
                );
                FileInfo info = null;
                while ((info = enumerator.next_file ()) != null) {
                    File file = enumerator.get_child (info);
                    if (
                        file.query_file_type (0) == 1
                        && Tools.get_filename (file).has_suffix (".mplstyle")
                    ) add_user_style (file);
                }
                enumerator.close ();
                FileMonitor style_monitor = style_dir.monitor_directory (
                    FileMonitorFlags.NONE
                );
                style_monitor.changed.connect (on_file_change);
                style_monitor.ref ();
            } catch { assert_not_reached (); }
            application.style_manager.notify.connect (() => {
                if (!use_custom_style) {
                    handle_style_change ();
                }
            });
            FigureSettings figure_settings = application.data.figure_settings;
            figure_settings.bind_property (
                "use_custom_style",
                this,
                "use_custom_style",
                1 | 2
            );
            figure_settings.bind_property (
                "custom_style",
                this,
                "custom_style",
                1 | 2
            );
            selection_model.selection_changed.connect (() => {
                Style style = get_selected_style ();
                // Don't trigger unnecessary reloads
                if (style.file == null) { // System Style
                    if (use_custom_style) this.use_custom_style = false;
                } else {
                    if (style.name != custom_style) this.custom_style = style.name;
                    if (!use_custom_style) this.use_custom_style = true;
                }
            });
            handle_style_change ();
        }

        private void on_use_custom_style () {
            if (use_custom_style) {
                on_custom_style ();
            } else {
                selection_model.set_selected (0);
                handle_style_change (true);
            }
        }

        private void on_custom_style () {
            if (!use_custom_style) return;
            for (uint i = 1; i < style_model.get_n_items (); i++) {
                Style style = style_model.get_item (i) as Style;
                if (style.name == custom_style) {
                    selection_model.set_selected (i);
                    break;
                }
            }
            handle_style_change (true);
        }

        private void on_file_change (File file, File? other_file, FileMonitorEvent event_type) {
            if (file.get_basename ()[0] == '.') return;
            string? stylename = null;
            bool possible_visual_impact = true;
            switch (event_type) {
                case FileMonitorEvent.CREATED:
                    for (uint i = 1; i < style_model.get_n_items (); i++) {
                        Style style = style_model.get_item (i) as Style;
                        if (style.file.equal (file)) {
                            return;
                        }
                    }
                    add_user_style (file);
                    break;
                case FileMonitorEvent.DELETED:
                    for (uint i = 1; i < style_model.get_n_items (); i++) {
                        Style style = style_model.get_item (i) as Style;
                        if (style.file.equal (file)) {
                            stylenames.remove (style.name);
                            style_model.remove (i);
                            stylename = style.name;
                        }
                    }
                    possible_visual_impact = stylename != null;
                    break;
                case FileMonitorEvent.CHANGES_DONE_HINT:
                    Style tmp_style = style_request.emit (file);
                    for (uint i = 1; i < style_model.get_n_items (); i++) {
                        Style style = style_model.get_item (i) as Style;
                        if (style.file.equal (file)) {
                            style.name = tmp_style.name;
                            style.preview = tmp_style.preview;
                            style.light = tmp_style.light;
                            stylename = tmp_style.name;
                            break;
                        }
                    }
                    possible_visual_impact = true;
                    break;
                default:
                    return;
            }
            if (possible_visual_impact
                && use_custom_style
                && custom_style == stylename) {
                handle_style_change ();
            }
        }

        private void handle_style_change (bool recolor_items = false) {
            notify_property ("selected_stylename");
            application.python_helper.run_method (this, "_update_system_style");
            application.python_helper.run_method (this, "_update_selected_style");
            style_changed.emit (recolor_items);
        }

        private void add_user_style (File file) {
            Style style = style_request.emit (file);
            if (stylenames.contains (style.name)) {
                style.name = Tools.get_duplicate_string (
                    style.name, stylenames.to_array ()
                );
            }
            CompareDataFunc<Style> cmp = style_cmp;
            style_model.insert_sorted (style, cmp);
            stylenames.add (style.name);
            if (use_custom_style) {
                string old_style = custom_style;
                if (!stylenames.contains (old_style)) {
                    this.custom_style = style.name;
                }
                for (uint i = 1; i < style_model.get_n_items (); i++) {
                    Style i_style = style_model.get_item (i) as Style;
                    if (i_style.name == custom_style) {
                        selection_model.set_selected (i);
                    }
                }
            }
        }

        protected Style get_selected_style () {
            return selection_model.get_selected_item () as Style;
        }

        /**
         * List all stylenames
         *
         * The result is guaranteed to be sorted and excludes the system style.
         */
        public string[] list_stylenames () {
            string[] stylenames = {};
            for (uint i = 1; i < style_model.get_n_items (); i++) {
                Style style = style_model.get_item (i) as Style;
                stylenames += style.name;
            }
            return stylenames;
        }

        public void copy_style (string template, string name) {
            string new_name = name;
            if (stylenames.contains (name)) {
                new_name = Tools.get_duplicate_string (
                    name, stylenames.to_array ()
                );
            }
            copy_request.emit (template, new_name);
        }
    }

    public class Style : Object {
        public string name { get; construct set; default = ""; }
        public Texture preview { get; set; }
        public File? file { get; construct set; }
        public bool mutable { get; construct set; }
        public bool light { get; set; default = true; }

        public Style (string name, File? file, Texture preview, bool mutable) {
            Object (
                name: name, file: file, preview: preview, mutable: mutable
            );
        }
    }

    /**
     * Style Preview widget
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-preview.ui")]
    private class StylePreview : Box {

        [GtkChild]
        private unowned Label label { get; }

        [GtkChild]
        private unowned Picture picture { get; }

        [GtkChild]
        public unowned Button edit_button { get; }

        [GtkChild]
        public unowned Button delete_button { get; }

        private Style _style;
        private CssProvider provider;

        public Style style {
            get { return this._style; }
            set {
                this._style = value;
                value.bind_property ("name", this, "stylename", 2);
                value.bind_property ("preview", this, "preview", 2);
            }
        }

        public string stylename {
            set { label.set_label (Tools.shorten_label (value)); }
        }

        public Texture preview {
            get { return picture.get_paintable () as Texture; }
            set {
                picture.set_paintable (value);
                if (_style.mutable) {
                    string color;
                    if (_style.light) {
                        color = "@light_1";
                    } else color = "@dark_5";
                    provider.load_from_string (@"button { color: $color; }");
                }
            }
        }

        construct {
            this.provider = new CssProvider ();
            edit_button.get_style_context ().add_provider (
                provider, STYLE_PROVIDER_PRIORITY_APPLICATION
            );
        }
    }

    /**
     * Add style dialog
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/add-style.ui")]
    public class AddStyleDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.EntryRow new_style_name { get; }

        [GtkChild]
        private unowned Adw.ComboRow style_templates { get; }

        private StyleManager style_manager;
        private string[] stylenames;

        public signal void accept (string template, string name);

        public AddStyleDialog (StyleManager style_manager, Widget parent) {
            this.style_manager = style_manager;
            this.stylenames = style_manager.list_stylenames ();
            style_templates.set_model (new StringList (stylenames));
            if (style_manager.use_custom_style) {
                string template = style_manager.custom_style;
                for (uint i = 0; i < stylenames.length; i++) {
                    if (stylenames[i] == template) {
                        style_templates.set_selected (i);
                        break;
                    }
                }
            }
            present (parent);
        }

        private string get_selected () {
            var item = style_templates.get_selected_item () as StringObject;
            return item.get_string ();
        }

        [GtkCallback]
        private void on_template_changed () {
            new_style_name.set_text (
                Tools.get_duplicate_string (get_selected (), stylenames)
            );
        }

        [GtkCallback]
        private void on_accept () {
            accept.emit (get_selected (), new_style_name.get_text ());
            close ();
        }
    }
}
