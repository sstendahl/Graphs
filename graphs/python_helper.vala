// SPDX-License-Identifier: GPL-3.0-or-later
// Python Helper - Vala Part
namespace Graphs {
    public class PythonHelper : Object {
        public Application application { protected get; construct set; }

        protected signal FigureSettingsDialog figure_settings_dialog_request ();
        public FigureSettingsDialog create_figure_settings_dialog () {
            return this.figure_settings_dialog_request.emit ();
        }

        protected signal ItemBox item_box_request (Item item, int index);
        public ItemBox create_item_box (Item item, int index) {
            return this.item_box_request.emit (item, index);
        }
    }
}