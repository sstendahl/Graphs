// SPDX-License-Identifier: GPL-3.0-or-later
using Gtk;
using Adw;

namespace Graphs {
    /**
     * Style Editor Window window
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor-window.ui")]
    public class StyleEditor : Adw.ApplicationWindow {
        [GtkChild]
        protected unowned Adw.OverlaySplitView split_view { get; }

        [GtkChild]
        protected unowned Adw.Clamp editor_clamp { get; }

        [GtkChild]
        protected unowned Adw.ToolbarView content_view { get; }

        [GtkChild]
        protected unowned Adw.HeaderBar content_headerbar { get; }

        private File _file;

        protected signal void load_request (File file);
        protected signal void save_request (File file);

        public void load (File file) {
            this._file = file;
            load_request.emit (file);
        }

        public void save (File file) {
            save_request.emit (file);
        }

        public override bool close_request () {
            save_request.emit (_file);
            var application = application as Application;
            application.on_style_editor_closed (this);
            return false;
        }
    }
}
