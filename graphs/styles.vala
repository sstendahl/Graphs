// SPDX-License-Identifier: GPL-3.0-or-later
using Gdk;
using Gee;
using Gtk;

namespace Graphs {
    public int style_cmp (Style a, Style b) {
        if (a.file == null) return -1;
        else if (b.file == null) return 1;
        return strcmp (a.name.down (), b.name.down ());
    }

    public string filename_from_stylename (string name) {
        var filename = name.replace (" ", "-");
        filename = filename.replace ("(", "");
        filename = filename.replace (")", "");
        filename = filename.down ();
        return filename + ".mplstyle";
    }

    private bool filter_system_style (Object style) {
        return ((Style) style).file != null;
    }

    /**
     * Style manager
     */
    public class StyleManager : Object {
        public static GLib.ListStore style_model { get; private set; }
        public static FilterListModel filtered_style_model { get; private set; }
        public static File style_dir { get; private set; }
        public signal void style_changed (string stylename);
        public signal void style_deleted (string stylename);
        public signal void style_renamed (string old_name, string new_name);

        protected signal void create_style_request (Style template, File destination, string name);
        protected signal Style style_request (File file);

        public static StyleManager instance { get; private set; }

        protected void setup (string system_style, StyleManager instance) {
            StyleManager.instance = instance;
            style_model = new GLib.ListStore (typeof (Style));
            filtered_style_model = new FilterListModel (
                style_model, new CustomFilter (filter_system_style)
            );
            try {
                File config_dir = Tools.get_config_directory ();
                style_dir = config_dir.get_child_for_display_name ("styles");
                if (!style_dir.query_exists ()) {
                    style_dir.make_directory_with_parents ();
                }
            } catch {
                assert_not_reached ();
            }
            style_model.append (
                new Style (
                    _("System"),
                    null,
                    Gdk.Texture.from_resource (
                        @"/se/sjoerd/Graphs/system-style-$system_style.png"
                    ),
                    false
                )
            );
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
            try {
                FileEnumerator enumerator = style_dir.enumerate_children (
                    "standard::*",
                    FileQueryInfoFlags.NONE
                );
                Gee.List<string> stylenames = new Gee.ArrayList<string>.wrap (list_stylenames ());
                CompareDataFunc<Style> cmp = style_cmp;
                FileInfo info = null;
                while ((info = enumerator.next_file ()) != null) {
                    File file = enumerator.get_child (info);
                    if (
                        file.query_file_type (0) == 1
                        && Tools.get_filename (file).has_suffix (".mplstyle")
                    ) {
                        Style style = instance.style_request.emit (file);
                        style.name = Tools.get_duplicate_string (
                            style.name, stylenames.to_array ()
                        );
                        style_model.insert_sorted (style, cmp);
                        stylenames.add (style.name);
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

        private async static void on_file_change (File file, File? other_file, FileMonitorEvent event_type) {
            if (file.get_basename ()[0] == '.') return;
            Style? style = null;
            switch (event_type) {
                case FileMonitorEvent.DELETED:
                    var index = find_style_for_file (file, out style);
                    if (index == -1) return;
                    style_model.remove (index);
                    instance.style_deleted.emit (style.name);
                    return;
                case FileMonitorEvent.CHANGES_DONE_HINT:
                    find_style_for_file (file, out style);
                    if (style == null) {
                        style = instance.style_request.emit (file);
                        style.name = Tools.get_duplicate_string (
                            style.name, list_stylenames ()
                        );
                        CompareDataFunc<Style> cmp = style_cmp;
                        style_model.insert_sorted (style, cmp);
                        return;
                    }
                    Style tmp_style = instance.style_request.emit (file);
                    style.preview = tmp_style.preview;
                    style.light = tmp_style.light;
                    if (style.name == tmp_style.name) {
                        instance.style_changed.emit (style.name);
                        return;
                    }
                    string old_name = style.name;
                    style.name = Tools.get_duplicate_string (
                        tmp_style.name, list_stylenames ()
                    );
                    instance.style_renamed.emit (old_name, style.name);
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
        public static string[] list_stylenames () {
            string[] stylenames = new string[filtered_style_model.get_n_items ()];
            for (uint i = 0; i < filtered_style_model.get_n_items (); i++) {
                Style style = (Style) filtered_style_model.get_item (i);
                stylenames[i] = style.name;
            }
            return (owned) stylenames;
        }

        public static File create_style (uint template, string name) {
            string new_name = Tools.get_duplicate_string (
                name, list_stylenames ()
            );
            var style = style_model.get_item (template) as Style;
            var filename = filename_from_stylename (new_name);
            try {
                var destination = style_dir.get_child_for_display_name (filename);
                instance.create_style_request.emit (style, destination, new_name);
                return destination;
            } catch { assert_not_reached (); }
        }

        private static int find_style_for_file (File file, out Style? style) {
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
            set { label.set_label (value); }
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

    public async void import_style (Gtk.Window window) {
        var dialog = new FileDialog ();
        dialog.set_filters (get_mplstyle_file_filters ());
        try {
            var file = yield dialog.open (window, null);
            string filename = Tools.get_filename (file);
            if (!filename.has_suffix (".mplstyle")) return;
            var style_dir = StyleManager.style_dir;
            var destination = style_dir.get_child_for_display_name (filename);
            uint i = 1;
            while (destination.query_exists ()) {
                var new_filename = new StringBuilder ();
                new_filename
                    .append (filename[:-9])
                    .append ("-")
                    .append (i.to_string ())
                    .append (".mplstyle");
                destination = style_dir.get_child_for_display_name (new_filename.free_and_steal ());
                i++;
            }
            file.copy_async.begin (destination, FileCopyFlags.NONE);
        } catch {}
    }
}
