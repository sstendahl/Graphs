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
        public unowned Adw.OverlaySplitView split_view { get; }

        [GtkChild]
        public unowned Adw.Clamp editor_clamp { get; }

        [GtkChild]
        public unowned Adw.ToolbarView content_view { get; }

        [GtkChild]
        public unowned Adw.HeaderBar content_headerbar { get; }
    }
}
