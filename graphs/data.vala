// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * Data class
     */
    public class Data : Object {
        protected Settings settings { get; set; }
        public FigureSettings figure_settings { get; construct set; }
        public bool can_undo { get; protected set; default = false; }
        public bool can_redo { get; protected set; default = false; }
        public bool can_view_back { get; protected set; default = false; }
        public bool can_view_forward { get; protected set; default = false; }
        public File file { get; set; }
        public bool unsaved { get; set; default = false; }

        private bool[] _used_positions;

        public signal void add_history_state_request ();

        public bool[] get_used_positions () {
            return this._used_positions;
        }

        public void set_used_positions (bool a, bool b, bool c, bool d) {
            this._used_positions = { a, b, c, d };
        }

        public signal void saved ();
    }
}
