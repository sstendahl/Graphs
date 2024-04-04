// SPDX-License-Identifier: GPL-3.0-or-later
using Gdk;
using Gtk;

namespace Graphs {
    public interface StyleManagerInterface : Object {
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

    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style_preview.ui")]
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

    public class PreviewWidgetHandler : Object {
        public SignalListItemFactory factory { get; construct set; }
        public signal void edit_request (Style style);

        construct {
            this.factory = new SignalListItemFactory ();
            this.factory.setup.connect (on_setup);
            this.factory.bind.connect (on_bind);
        }

        private void on_setup (Object object) {
            ListItem item = (ListItem) object;
            item.set_child (new StylePreview ());
        }

        private void on_bind (Object object) {
            ListItem item = (ListItem) object;
            StylePreview preview = (StylePreview) item.get_child ();
            Style style = (Style) item.get_item ();
            preview.style = style;
            if (style.mutable && !preview.edit_button.get_visible ()) {
                preview.edit_button.set_visible (true);
                preview.edit_button.clicked.connect (() => {
                    this.edit_request (style);
                });
            }
        }
    }
}
