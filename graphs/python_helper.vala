// SPDX-License-Identifier: GPL-3.0-or-later
// Python Helper - Vala Part
using Gtk;

namespace Graphs {
    public class PythonHelper : Object {
        public Application application { protected get; construct set; }

        protected signal FigureSettingsDialog figure_settings_dialog_request ();
        public FigureSettingsDialog create_figure_settings_dialog () {
            return this.figure_settings_dialog_request.emit ();
        }

        protected signal Widget edit_item_dialog_request (Item item);
        public Widget create_edit_item_dialog (Item item) {
            return this.edit_item_dialog_request.emit (item);
        }

        protected signal CurveFittingDialog curve_fitting_dialog_request (Item item);
        public CurveFittingDialog create_curve_fitting_dialog (Item item) {
            return this.curve_fitting_dialog_request.emit (item);
        }
    }
}
