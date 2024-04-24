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
        public bool use_custom_style { get; set; default = false; }
        public string custom_style { get; set; default = "Adwaita"; }
        public SingleSelection selection_model { get; set; }
        public File style_dir { get; construct set; }
        public string selected_stylename { get; protected set; }

        private GLib.ListStore style_model;

        construct {
            this.style_model = new GLib.ListStore (typeof (Style));
            this.selection_model = new SingleSelection (this.style_model);
            try {
                File config_dir = Tools.get_config_directory ();
                this.style_dir = config_dir.get_child_for_display_name ("styles");
                if (!this.style_dir.query_exists ()) {
                    this.style_dir.make_directory_with_parents ();
                }
            } catch {
                assert_not_reached ();
            }
        }

        protected string[] load_system_styles (string system_style) {
            string[] stylenames = {};
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
                    stylenames += name;
                    string preview_name = info.get_name ().replace (".mplstyle", ".png");
                    var preview = Gdk.Texture.from_resource (
                        @"/se/sjoerd/Graphs/$preview_name"
                    );
                    CompareDataFunc<Style> cmp = style_cmp;
                    this.style_model.insert_sorted (
                        new Style (name, file, preview, false),
                        cmp
                    );
                }
            } catch {
                assert_not_reached ();
            }
            this.style_model.insert (
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
            return stylenames;
        }

        protected Style get_selected_style () {
            return (Style) this.selection_model.get_selected_item ();
        }

        protected void setup_bindings (FigureSettings figure_settings) {
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
            this.selection_model.selection_changed.connect (() => {
                Style style = get_selected_style ();
                // Don't trigger unnecessary reloads
                if (style.file == null) { // System Style
                    if (this.use_custom_style) this.use_custom_style = false;
                } else {
                    if (style.name != this.custom_style) this.custom_style = style.name;
                    if (!this.use_custom_style) this.use_custom_style = true;
                }
            });
        }

        /**
         * List all stylenames
         *
         * The result is guaranteed to be sorted and excludes the system style.
         */
        public string[] list_stylenames () {
            string[] stylenames = {};
            for (uint i = 1; i < this.style_model.get_n_items (); i++) {
                Style style = (Style) this.style_model.get_item (i);
                stylenames += style.name;
            }
            return stylenames;
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
            set { this.label.set_label (Tools.shorten_label (value)); }
        }

        public Texture preview {
            get { return (Texture)this.picture.get_paintable (); }
            set {
                this.picture.set_paintable (value);
                if (this._style.mutable) {
                    string color;
                    if (this._style.light) {
                        color = "@light_1";
                    } else color = "@dark_5";
                    this.provider.load_from_string (@"button { color: $color; }");
                }
            }
        }

        construct {
            this.provider = new CssProvider ();
            this.edit_button.get_style_context ().add_provider (
                this.provider, STYLE_PROVIDER_PRIORITY_APPLICATION
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
            this.style_templates.set_model (new StringList (this.stylenames));
            if (style_manager.use_custom_style) {
                string template = style_manager.custom_style;
                for (uint i = 0; i < this.stylenames.length; i++) {
                    if (this.stylenames[i] == template) {
                        this.style_templates.set_selected (i);
                        break;
                    }
                }
            }
            present (parent);
        }

        private string get_selected () {
            var item = (StringObject) this.style_templates.get_selected_item ();
            return item.get_string ();
        }

        [GtkCallback]
        private void on_template_changed () {
            this.new_style_name.set_text (
                Tools.get_duplicate_string (get_selected (), this.stylenames)
            );
        }

        [GtkCallback]
        private void on_accept () {
            this.accept.emit (get_selected (), this.new_style_name.get_text ());
            close ();
        }
    }
}
