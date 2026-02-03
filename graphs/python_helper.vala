// SPDX-License-Identifier: GPL-3.0-or-later
// Python Helper - Vala Part
using Gtk;

namespace Graphs {
    public class PythonHelper : Object {
        public Application application { protected get; construct set; }

        protected signal Item add_equation_request (Window window, string name);
        public Item add_equation (Window window, string name) {
            return add_equation_request.emit (window, name);
        }

        protected signal void create_item_settings_request (EditItemPage page, Item item);
        public void create_item_settings (EditItemPage page, Item item) {
            create_item_settings_request.emit (page, item);
        }

        protected signal StyleEditor create_style_editor_request ();
        public StyleEditor create_style_editor () {
            return create_style_editor_request.emit ();
        }

        protected signal Window create_window_request ();
        public Window create_window () {
            return create_window_request ();
        }

        protected signal CurveFittingDialog curve_fitting_dialog_request (Window window, Item item);
        public CurveFittingDialog create_curve_fitting_dialog (Window window, Item item) {
            return curve_fitting_dialog_request.emit (window, item);
        }

        protected signal void export_items_request (Window window, string mode, File file, Item[] items);
        public void export_items (Window window, string mode, File file, Item[] items) {
            export_items_request.emit (window, mode, file, items);
            window.add_toast_string_with_file (
                _("Exported Data"), file
            );
        }

        public signal void export_figure_request (File file, GLib.Settings settings, Data data);
        public void export_figure (File file, GLib.Settings settings, Data data) {
            this.export_figure_request.emit (file, settings, data);
        }

        protected signal Item generate_data_request (Window window, string name);
        public Item generate_data (Window window, string name) {
            return generate_data_request.emit (window, name);
        }

        protected signal void perform_operation_request (Window window, string name);
        public void perform_operation (Window window, string name) {
            perform_operation_request.emit (window, name);
        }

        protected signal void python_method_request (Object object, string method);
        public void run_method (Object object, string method) {
            python_method_request.emit (object, method);
        }

        protected signal bool validate_equation_request (string input);
        public bool validate_equation (string input) {
            return validate_equation_request.emit (input);
        }
    }
}
