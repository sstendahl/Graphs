// SPDX-License-Identifier: GPL-3.0-or-later
using Gee;

namespace Graphs {
    /**
     * Data class
     */
    public class Data : Object, ListModel, Traversable<Item>, Iterable<Item> {
        protected Settings settings { get; set; }
        public FigureSettings figure_settings { get; construct set; }
        public bool can_undo { get; protected set; default = false; }
        public bool can_redo { get; protected set; default = false; }
        public bool can_view_back { get; protected set; default = false; }
        public bool can_view_forward { get; protected set; default = false; }
        public File file { get; set; }
        public bool unsaved { get; set; default = false; }
        public string project_name { get; protected set; }
        public string project_path { get; protected set; }
        public bool items_selected {
            get {
                foreach (Item item in this._items) {
                    if (item.selected) return true;
                }
                return false;
            }
        }

        private bool[] _used_positions;
        private Gee.AbstractList<Item> _items;

        protected signal void python_method_request (string method);
        protected signal void position_changed (uint index1, uint index2);
        protected signal void item_changed (Item item, string prop_name);
        protected signal void delete_request (Item[] items);

        construct {
            this._items = new Gee.LinkedList<Item> ();
            this.items_changed.connect (() => {
                this._update_used_positions ();
                this.notify_property ("items_selected");
            });
        }

        public Type get_item_type () {
            return typeof (Item);
        }

        public void reset () {
            this.python_method_request.emit ("_reset");
            uint removed = this._items.size;
            this._items.clear ();
            this.file = null;
            this.unsaved = false;
            this.python_method_request.emit ("_initialize");
            this.items_changed.emit (0, removed, 0);
        }

        public bool is_empty () {
            return this._items.size == 0;
        }

        public Item[] get_items () {
            return this._items.to_array ();
        }

        protected void _add_item (Item item, bool notify) {
            item.notify["selected"].connect (this._on_item_selected);
            item.notify.connect (this._on_item_change);
            item.notify["xposition"].connect (this._on_item_position_change);
            item.notify["yposition"].connect (this._on_item_position_change);
            this._items.add (item);
            if (notify) {
                this.items_changed.emit (this._items.size - 1, 0, 1);
            }
        }

        protected void _remove_item (Item item) {
            uint index = this.index (item);
            this._items.remove_at ((int) index);
            this.items_changed.emit (index, 1, 0);
        }

        public void delete_items (Item[] items) {
            this.delete_request.emit (items);
        }

        private void _on_item_selected () {
            this.notify_property ("items_selected");
        }

        private void _on_item_change (Object item, ParamSpec spec) {
            this.item_changed.emit ((Item) item, spec.name);
        }

        private void _on_item_position_change () {
            this.optimize_limits ();
            this._update_used_positions ();
            this.items_changed.emit (0, 0, 0);
        }

        public void set_items (Item[] items) {
            uint removed = this._items.size;
            this._items.clear ();
            foreach (Item item in items) {
                this._add_item (item, false);
            }
            this._update_used_positions ();
            this.items_changed.emit (0, removed, this._items.size);
        }

        public string[] get_names () {
            string[] names = {};
            foreach (Item item in this._items) {
                names += item.name;
            }
            return names;
        }

        public uint index (Item item) {
            return this._items.index_of (item);
        }

        public uint get_n_items () {
            return this._items.size;
        }

        public Object? get_item (uint position) {
            return this._items[(int) position];
        }

        public Item? get_for_uuid (string uuid) {
            foreach (Item item in this._items) {
                if (item.uuid == uuid) return item;
            }
            return null;
        }

        public bool[] get_used_positions () {
            return this._used_positions;
        }

        protected void _update_used_positions () {
            if (this._items.size == 0) {
                this._used_positions = {true, false, true, false};
                return;
            }
            bool[] used_positions = {false, false, false, false};
            foreach (Item item in this._items) {
                if (this.figure_settings.hide_unselected && !item.selected)
                continue;
                used_positions[item.xposition] = true;
                used_positions[item.yposition] = true;
            }
            this._used_positions = used_positions;
        }

        public Iterator<Item> iterator () {
            return this._items.iterator ();
        }

        public bool @foreach (ForallFunc<Item> f) {
            return this._items.foreach (f);
        }

        protected string get_version () {
            return Config.VERSION;
        }

        public void change_position (uint index1, uint index2) {
            if (index1 == index2) return;
            Item item = this._items[(int) index2];
            this._items.remove_at ((int) index2);
            this._items.insert ((int) index1, item);
            uint position = uint.min (index1, index2);
            uint changed = uint.max (index1, index2) - position;
            this.items_changed.emit (position, changed, changed);
            this.position_changed.emit (index1, index2);
        }

        public void optimize_limits () {
            this.python_method_request.emit ("_optimize_limits");
        }

        public void add_history_state () {
            this.python_method_request.emit ("_add_history_state");
        }

        public void undo () {
            this.python_method_request.emit ("_undo");
        }

        public void redo () {
            this.python_method_request.emit ("_redo");
        }

        public void add_view_history_state () {
            this.python_method_request.emit ("_add_view_history_state");
        }

        public void view_back () {
            this.python_method_request.emit ("_view_back");
        }

        public void view_forward () {
            this.python_method_request.emit ("_view_forward");
        }

        public void save () {
            this.python_method_request.emit ("_save");
        }

        public void load () {
            this.python_method_request.emit ("_load");
        }
    }
}
