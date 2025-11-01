// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    /**
     * Add style dialog
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/style-editor/add-style.ui")]
    public class AddStyleDialog : Adw.Dialog {

        [GtkChild]
        private unowned Adw.EntryRow new_style_name { get; }

        [GtkChild]
        private unowned Adw.ComboRow style_templates { get; }

        public signal void accept (File file);

        private StyleManager style_manager;

        public AddStyleDialog (StyleManager style_manager, Widget parent) {
            this.style_manager = style_manager;
            style_templates.set_expression (new PropertyExpression (typeof (Style), null, "name"));
            style_templates.set_model (style_manager.filtered_style_model);
            present (parent);
        }

        [GtkCallback]
        private void on_template_changed () {
            string[] stylenames = style_manager.list_stylenames ();
            string template = stylenames[style_templates.get_selected ()];
            new_style_name.set_text (Tools.get_duplicate_string (template, stylenames));
        }

        [GtkCallback]
        private void on_accept () {
            uint template = style_templates.get_selected () + 1;
            var file = style_manager.create_style (template, new_style_name.get_text ());
            close ();
            accept.emit (file);
        }
    }
}
