// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public interface DataInterface : Object {
        public abstract FigureSettings figure_settings { get; construct set; }
        public abstract bool can_undo { get; }
        public abstract bool can_redo { get; }
        public abstract bool can_view_back { get; }
        public abstract bool can_view_forward { get; }
        public abstract bool items_selected { get; }
        public abstract bool empty { get; }

        public abstract Item[] items { get; set; }

        public abstract int index (Item item);
        public abstract string[] get_names ();
        public abstract int get_n_items ();
        public abstract Item get_at_pos (int position);
        public abstract Item get_for_uuid (string uuid);

        public abstract void change_position (int index1, int index2);
        public abstract void add_items (Item[] items, StyleManagerInterface style_manager);
        public abstract void delete_items (Item[] items);

        public abstract void add_history_state (double[]? old_limits=null);
        public abstract void undo ();
        public abstract void redo ();

        public abstract void add_view_history_state ();
        public abstract void view_back ();
        public abstract void view_forward ();

        public abstract void optimize_limits ();
    }
}
