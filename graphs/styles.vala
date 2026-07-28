// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public int style_cmp (Style a, Style b) {
        if (a.file == null) return -1;
        else if (b.file == null) return 1;
        return strcmp (a.name.down (), b.name.down ());
    }

    private string filename_from_stylename (string name) {
        var filename = name.replace (" ", "-");
        filename = filename.replace ("(", "");
        filename = filename.replace (")", "");
        filename = filename.down ();
        return filename + ".mplstyle";
    }

    private bool filter_system_style (Object style) {
        return ((Style) style).file != null;
    }

    private struct StyleInfo {
        public string name;
        public string style_path;
        public string preview_path;
    }

    public class StyleParameters : Object {
        private HashTable<string, Value?> parameters = new HashTable<string, Value?> (str_hash, str_equal);

        public void set_param (string key, Value? val) {
            if (val == null) return;
            parameters.set (key, val);
        }

        public Value get_param (string key) {
            return parameters.get (key);
        }

        public unowned string get_name () {
            return (string) parameters.get ("name");
        }

        public unowned string get_color () {
            return (string) parameters.get ("text.color");
        }

        public unowned string get_background_color () {
            return (string) parameters.get ("figure.facecolor");
        }

        public unowned string[] get_color_cycle () {
            return (string[]) parameters.get ("axes.prop_cycle");
        }

        public unowned string[] get_errorbar_cycle () {
            return (string[]) parameters.get ("errorbar.color_cycle");
        }

        public string[] get_params () {
            return parameters.get_keys_as_array ();
        }
    }

    private const string SYSTEM_CSS_TEMPLATE = ".system-canvas-view {color: %s; background-color: %s;}";

    /**
     * Style manager
     */
    public class StyleManager : Object {
        public static ListStore style_model { get; private set; }
        public static Gtk.FilterListModel filtered_style_model { get; private set; }
        public static File style_dir { get; private set; }
        public signal void style_changed (string stylename);
        public signal void style_deleted (string stylename);
        public signal void style_renamed (string old_name, string new_name);

        protected signal Gdk.Texture preview_request (StyleParameters parameters);
        protected signal StyleParameters params_request (File file, StyleParameters? validate);
        protected signal void save_request (StyleParameters parameters, File file);

        public static StyleManager instance { get; private set; }

        private Gtk.CssProvider css_provider;
        private StyleParameters system_style_light_params;
        private StyleParameters system_style_dark_params;

        construct {
            this.css_provider = new Gtk.CssProvider ();
            Gtk.StyleContext.add_provider_for_display (
                Gdk.Display.get_default (), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            );
        }

        protected void setup () {
            StyleManager.instance = this;

            string gtk_theme = Gtk.Settings.get_default ().gtk_theme_name.down ();
            bool ubuntu = Environment.get_variable ("SNAP") != null && gtk_theme.has_prefix ("yaru");

            unowned string system_style = ubuntu ? "yaru" : "adwaita";

            system_style_light_params = params_for_system_style (system_style);
            system_style_dark_params = params_for_system_style (system_style + "-dark");

            Adw.StyleManager.get_default ().notify.connect (on_system_style);
            on_system_style.begin ();

            style_model = new ListStore (typeof (Style));
            filtered_style_model = new Gtk.FilterListModel (
                style_model, new Gtk.CustomFilter (filter_system_style)
            );

            try {
                File config_dir = Tools.get_config_directory ();
                style_dir = config_dir.get_child_for_display_name ("styles");
                if (!style_dir.query_exists ()) {
                    style_dir.make_directory_with_parents ();
                }
            } catch { assert_not_reached (); }

            style_model.append (new Style () {
                name = _("System"),
                preview = Gdk.Texture.from_resource (@"/se/sjoerd/Graphs/system-style-$system_style.png"),
                mutable = false,
            });

            for (uint i = 0; i < STYLES.length; i++) {
                StyleInfo* info = &STYLES[i];
                style_model.append (new Style () {
                    name = info->name,
                    file = File.new_for_uri ("resource://" + info->style_path),
                    preview = Gdk.Texture.from_resource (info->preview_path),
                    mutable = false,
                });
            }

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
                        Style style = style_for_file (file);
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
            } catch {}
        }

        private static Style style_for_file (File file) {
            var parameters = get_style_params (file, get_system_style_params ());
            return new Style () {
                name = parameters.get_name (),
                file = file,
                preview = instance.preview_request.emit (parameters),
                mutable = true,
                light = Tools.get_luminance_from_hex ((string) parameters.get_param ("axes.facecolor")) < 0.4,
            };
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
                        style = style_for_file (file);
                        style.name = Tools.get_duplicate_string (
                            style.name, list_stylenames ()
                        );
                        CompareDataFunc<Style> cmp = style_cmp;
                        style_model.insert_sorted (style, cmp);
                        return;
                    }
                    Style tmp_style = style_for_file (file);
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

        private async void on_system_style () {
            var style_params = get_system_style_params ();
            string css = SYSTEM_CSS_TEMPLATE.printf (style_params.get_color (), style_params.get_background_color ());
            css_provider.load_from_string (css);
        }

        public static StyleParameters get_system_style_params () {
            return Adw.StyleManager.get_default ().get_dark () ? instance.system_style_dark_params : instance.system_style_light_params;
        }

        public static StyleParameters get_style_params (File file, StyleParameters? validate = null) {
            return instance.params_request.emit (file, validate);
        }

        public static void save_style_params (StyleParameters parameters, File file) {
            instance.save_request.emit (parameters, file);
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
            var style = (Style) style_model.get_item (template);
            var filename = filename_from_stylename (new_name);
            try {
                var destination = style_dir.get_child_for_display_name (filename);
                var parameters = get_style_params (style.file, get_system_style_params ());
                parameters.set_param ("name", new_name);
                PythonHelper.run_method (parameters, "update");
                instance.save_request.emit (parameters, destination);
                return destination;
            } catch { assert_not_reached (); }
        }

        private static int find_style_for_file (File file, out Style? style) {
            for (uint i = 1; i < style_model.get_n_items (); i++) {
                Style i_style = (Style) style_model.get_item (i);
                if (i_style.file.equal (file)) {
                    style = i_style;
                    return (int) i;
                }
            }
            style = null;
            return -1;
        }

        private StyleParameters params_for_system_style (string name) {
            File file = File.new_for_uri (@"resource:///se/sjoerd/Graphs/styles/$name.mplstyle");
            return params_request.emit (file, null);
        }
    }

    public class Style : Object {
        public string name { get; construct set; default = ""; }
        public Gdk.Texture preview { get; set; }
        public File? file { get; construct set; }
        public bool mutable { get; construct set; }
        public bool light { get; set; default = true; }
    }

    /**
     * Style Preview widget
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-preview.ui")]
    private class StylePreview : Adw.Bin {

        [GtkChild]
        private unowned Gtk.Label label { get; }

        [GtkChild]
        private unowned Gtk.Picture picture { get; }

        [GtkChild]
        public unowned Gtk.MenuButton menu_button { get; }

        private Style _style;
        private Gtk.CssProvider provider;

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

        public Gdk.Texture preview {
            get { return (Gdk.Texture) picture.get_paintable (); }
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
            this.provider = new Gtk.CssProvider ();
            menu_button.get_style_context ().add_provider (
                provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            );
        }
    }

    public async void import_style (Gtk.Window window) {
        var dialog = new Gtk.FileDialog ();
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
