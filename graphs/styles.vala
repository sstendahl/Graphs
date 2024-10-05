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
        public GLib.ListStore style_model { get; construct set; }
        public File style_dir { get; construct set; }
        public signal void style_changed (Style style);

        private Gee.AbstractSet<string> stylenames { get; private set; }

        protected signal void copy_request (string template, string name);
        protected signal Style style_request (File file);

        construct {
            this.style_model = new GLib.ListStore (typeof (Style));
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
            application.style_manager.notify.connect (() => {
                application.python_helper.run_method (this, "_update_system_style");
            });
        }

        protected void setup (string system_style) {
            File style_list = File.new_for_uri ("resource:///se/sjoerd/Graphs/styles.txt");
            try {
                var stream = new DataInputStream (style_list.read ());
                string line;
                while ((line = stream.read_line (null)) != null) {
                    string[] strings = line.chomp ().split (";", 3);
                    style_model.append (
                        new Style (
                            strings[0],
                            File.new_for_uri ("resource://" + strings[1]),
                            Gdk.Texture.from_resource (strings[2]),
                            false
                        )
                    );
                }
            } catch { assert_not_reached (); }
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
        }

        private void on_file_change (File file, File? other_file, FileMonitorEvent event_type) {
            if (file.get_basename ()[0] == '.') return;
            Style style = null;
            switch (event_type) {
                case FileMonitorEvent.CREATED:
                    if (find_style_for_file (file, out style) > 0) return;
                    add_user_style (file);
                    style_changed.emit (style);
                    break;
                case FileMonitorEvent.DELETED:
                    var index = find_style_for_file (file, out style);
                    if (index == -1) return;
                    stylenames.remove (style.name);
                    style_model.remove (index);
                    style_changed.emit (style);
                    break;
                case FileMonitorEvent.CHANGES_DONE_HINT:
                    Style tmp_style = style_request.emit (file);
                    find_style_for_file (file, out style);
                    if (style == null) return;
                    style.name = tmp_style.name;
                    style.preview = tmp_style.preview;
                    style.light = tmp_style.light;
                    style_changed.emit (style);
                    break;
                default:
                    return;
            }
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

        private int find_style_for_file (File file, out Style? style) {
            for (uint i = 1; i < style_model.get_n_items (); i++) {
                Style i_style = style_model.get_item (i) as Style;
                if (i_style.file.equal (file)) {
                    style = i_style;
                    return (int) i;
                }
            }
            style = null;
            return -1;
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
        public unowned MenuButton menu_button { get; }

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
                    provider.load_from_string (@"menubutton { color: $color; }");
                }
            }
        }

        construct {
            this.provider = new CssProvider ();
            menu_button.get_style_context ().add_provider (
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

        public AddStyleDialog (StyleManager style_manager, Widget parent, FigureSettings figure_settings) {
            this.style_manager = style_manager;
            this.stylenames = style_manager.list_stylenames ();
            style_templates.set_model (new StringList (stylenames));
            if (figure_settings.use_custom_style) {
                string template = figure_settings.custom_style;
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
