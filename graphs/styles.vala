// SPDX-License-Identifier: GPL-3.0-or-later
using Gdk;
using Gtk;

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
        public signal void style_changed (string stylename);
        public signal void style_deleted (string stylename);
        public signal void style_renamed (string old_name, string new_name);

        protected signal void create_style_request (Style template, string name);
        protected signal Style style_request (File file);

        construct {
            this.style_model = new GLib.ListStore (typeof (Style));
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
                string[] stylenames = list_stylenames ();
                CompareDataFunc<Style> cmp = style_cmp;
                FileInfo info = null;
                while ((info = enumerator.next_file ()) != null) {
                    File file = enumerator.get_child (info);
                    if (
                        file.query_file_type (0) == 1
                        && Tools.get_filename (file).has_suffix (".mplstyle")
                    ) {
                        Style style = style_request.emit (file);
                        style.name = Tools.get_duplicate_string (
                            style.name, stylenames
                        );
                        style_model.insert_sorted (style, cmp);
                        stylenames += style.name;
                    };
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
            Style? style = null;
            switch (event_type) {
                case FileMonitorEvent.DELETED:
                    var index = find_style_for_file (file, out style);
                    if (index == -1) return;
                    style_model.remove (index);
                    style_deleted.emit (style.name);
                    return;
                case FileMonitorEvent.CHANGES_DONE_HINT:
                    find_style_for_file (file, out style);
                    if (style == null) {
                        style = style_request.emit (file);
                        style.name = Tools.get_duplicate_string (
                            style.name, list_stylenames ()
                        );
                        CompareDataFunc<Style> cmp = style_cmp;
                        style_model.insert_sorted (style, cmp);
                        return;
                    }
                    Style tmp_style = style_request.emit (file);
                    style.preview = tmp_style.preview;
                    style.light = tmp_style.light;
                    if (style.name == tmp_style.name) {
                        style_changed.emit (style.name);
                        return;
                    }
                    string old_name = style.name;
                    style.name = Tools.get_duplicate_string (
                        tmp_style.name, list_stylenames ()
                    );
                    style_renamed.emit (old_name, style.name);
                    return;
                default:
                    return;
            }
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

        public void create_style (uint template, string name) {
            string new_name = Tools.get_duplicate_string (
                name, list_stylenames ()
            );
            var style = style_model.get_item (template) as Style;
            create_style_request.emit (style, new_name);
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
    private class StylePreview : Adw.Bin {

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
            uint template = style_templates.get_selected () + 1;
            style_manager.create_style (template, new_style_name.get_text ());
            close ();
        }
    }
}
