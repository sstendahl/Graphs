// SPDX-License-Identifier: GPL-3.0-or-later
using Gee;
using Gtk;

namespace Graphs {
    /**
     * Data class
     */
    public class Data : Object, ListModel, Traversable<Item>, Iterable<Item> {
        public Application application { get; construct set; }
        public FigureSettings figure_settings { get; private set; }
        public bool can_undo { get; protected set; default = false; }
        public bool can_redo { get; protected set; default = false; }
        public bool can_view_back { get; protected set; default = false; }
        public bool can_view_forward { get; protected set; default = false; }
        public File file { get; set; }
        public bool unsaved { get; set; default = false; }
        public string project_name { get; protected set; }
        public string project_path { get; protected set; }
        public SingleSelection style_selection_model { get; private set; }
        public bool items_selected {
            get {
                foreach (Item item in _items) {
                    if (item.selected) return true;
                }
                return false;
            }
        }
        public string selected_stylename {
            get { return this.get_selected_style ().name; }
        }

        private bool[] _used_positions;
        private Gee.AbstractList<Item> _items;

        public signal void style_changed (bool recolor_items);
        protected signal void python_method_request (string method);
        protected signal void position_changed (uint index1, uint index2);
        protected signal void item_changed (Item item, string prop_name);
        protected signal void delete_request (Item[] items);

        construct {
            this._items = new Gee.LinkedList<Item> ();
            items_changed.connect (() => {
                _update_used_positions ();
                notify_property ("items_selected");
            });
        }

        protected void setup () {
            this.figure_settings = new FigureSettings (application.get_settings_child ("figure"));

            var style_manager = application.figure_style_manager;
            this.style_selection_model = new SingleSelection (style_manager.style_model);

            application.style_manager.notify.connect (() => {
                if (!figure_settings.use_custom_style) {
                    handle_style_change ();
                }
            });

            style_selection_model.selection_changed.connect (() => {
                Style style = get_selected_style ();
                // Don't trigger unnecessary reloads
                if (style.file == null) { // System Style
                    if (figure_settings.use_custom_style) {
                        figure_settings.use_custom_style = false;
                    }
                } else {
                    if (style.name != figure_settings.custom_style) {
                        figure_settings.custom_style = style.name;
                    }
                    if (!figure_settings.use_custom_style) {
                        figure_settings.use_custom_style = true;
                    }
                }
            });

            figure_settings.notify["custom-style"].connect (_on_custom_style);
            figure_settings.notify["use-custom-style"].connect (_on_use_custom_style);

            handle_style_change ();
        }

        // Section ListModel
        // All required methods to implement the ListModel interface

        public Object? get_item (uint position) {
            return _items[(int) position];
        }

        public Type get_item_type () {
            return typeof (Item);
        }

        public uint get_n_items () {
            return _items.size;
        }

        // End section ListModel

        // Section management

        public void reset () {
            python_method_request.emit ("_reset");
            uint removed = _items.size;
            _items.clear ();
            this.file = null;
            this.unsaved = false;
            python_method_request.emit ("_initialize");
            items_changed.emit (0, removed, 0);
        }

        protected void _update_used_positions () {
            if (_items.size == 0) {
                _used_positions = {true, false, true, false};
                return;
            }
            bool[] used_positions = {false, false, false, false};
            foreach (Item item in _items) {
                if (figure_settings.hide_unselected && !item.selected)
                continue;
                used_positions[item.xposition] = true;
                used_positions[item.yposition + 2] = true;
            }
            _used_positions = used_positions;
        }

        protected void _add_item (Item item, int index = -1, bool notify = false) {
            if (index < 0) index = _items.size;
            item.notify["selected"].connect (_on_item_selected);
            item.notify.connect (_on_item_change);
            item.notify["xposition"].connect (_on_item_position_change);
            item.notify["yposition"].connect (_on_item_position_change);
            _items.insert (index, item);
            if (notify) items_changed.emit (index, 0, 1);
        }

        protected void _remove_item (Item item) {
            uint index = this.index (item);
            _items.remove_at ((int) index);
            items_changed.emit (index, 1, 0);
        }

        public void set_items (Item[] items) {
            uint removed = _items.size;
            _items.clear ();
            foreach (Item item in items) {
                _add_item (item);
            }
            _update_used_positions ();
            items_changed.emit (0, removed, _items.size);
        }

        public void delete_items (Item[] items) {
            delete_request.emit (items);
        }

        // End section management

        // Section style

        private void handle_style_change (bool recolor_items = false) {
            notify_property ("selected_stylename");
            python_method_request.emit ("_update_selected_style");
            style_changed.emit (recolor_items);
        }

        protected Style get_selected_style () {
            return style_selection_model.get_selected_item () as Style;
        }

        // End section style

        // Section Vala iterator

        public Iterator<Item> iterator () {
            return _items.iterator ();
        }

        public bool @foreach (ForallFunc<Item> f) {
            return _items.@foreach (f);
        }

        protected string get_version () {
            return Config.VERSION;
        }

        // End section Vala iterator

        // Section misc

        public bool is_empty () {
            return _items.size == 0;
        }

        public Item[] get_items () {
            return _items.to_array ();
        }

        public string[] get_names () {
            string[] names = {};
            foreach (Item item in _items) {
                names += item.name;
            }
            return names;
        }

        public uint index (Item item) {
            return _items.index_of (item);
        }

        public Item? get_for_uuid (string uuid) {
            foreach (Item item in _items) {
                if (item.uuid == uuid) return item;
            }
            return null;
        }

        public bool[] get_used_positions () {
            return _used_positions;
        }

        public void change_position (uint index1, uint index2) {
            if (index1 == index2) return;
            Item item = _items[(int) index2];
            _items.remove_at ((int) index2);
            _items.insert ((int) index1, item);
            uint position = uint.min (index1, index2);
            uint changed = uint.max (index1, index2) - position + 1;
            items_changed.emit (position, changed, changed);
            position_changed.emit (index1, index2);
        }

        public void optimize_limits () {
            python_method_request.emit ("_optimize_limits");
        }

        // End section misc

        // Section history

        public void add_history_state () {
            python_method_request.emit ("_add_history_state");
        }

        public void undo () {
            python_method_request.emit ("_undo");
        }

        public void redo () {
            python_method_request.emit ("_redo");
        }

        public void add_view_history_state () {
            python_method_request.emit ("_add_view_history_state");
        }

        public void view_back () {
            python_method_request.emit ("_view_back");
        }

        public void view_forward () {
            python_method_request.emit ("_view_forward");
        }

        // End section history

        // Section save & load

        public void save () {
            python_method_request.emit ("_save");
        }

        public void load () {
            python_method_request.emit ("_load");
        }

        // End section save & load

        // Section listeners

        private void _on_item_selected () {
            notify_property ("items_selected");
        }

        private void _on_item_change (Object item, ParamSpec spec) {
            item_changed.emit ((Item) item, spec.name);
        }

        private void _on_item_position_change () {
            optimize_limits ();
            _update_used_positions ();
            items_changed.emit (0, 0, 0);
        }

        private void _on_use_custom_style () {
            if (figure_settings.use_custom_style) {
                _on_custom_style ();
            } else {
                style_selection_model.set_selected (0);
                handle_style_change (true);
            }
        }

        private void _on_custom_style () {
            if (!figure_settings.use_custom_style) return;
            var style_model = style_selection_model.get_model ();
            for (uint i = 1; i < style_model.get_n_items (); i++) {
                Style style = style_model.get_item (i) as Style;
                if (style.name == figure_settings.custom_style) {
                    style_selection_model.set_selected (i);
                    break;
                }
            }
            handle_style_change (true);
        }

        // End section listeners
    }
}
