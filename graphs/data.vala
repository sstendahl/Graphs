// SPDX-License-Identifier: GPL-3.0-or-later
using Gee;
using Gtk;

namespace Graphs {
    /**
     * Data class
     */
    public class Data : Object, ListModel, SelectionModel, Traversable<Item>, Iterable<Item> {
        public bool can_undo { get; protected set; default = false; }
        public bool can_redo { get; protected set; default = false; }
        public bool can_view_back { get; protected set; default = false; }
        public bool can_view_forward { get; protected set; default = false; }
        public File file { get; set; }
        [CCode (notify = false)]
        public bool unsaved { get; set; default = false; }
        public SingleSelection style_selection_model { get; private set; }

        public string selected_stylename {
            get { return this.get_selected_style ().name; }
        }

        private FigureSettings _figure_settings;
        public FigureSettings figure_settings {
            get { return this._figure_settings; }
            protected set {
                this._figure_settings = value;
                value.notify["custom-style"].connect (_on_custom_style);
                value.notify["use-custom-style"].connect (_on_use_custom_style);
                value.notify.connect ((v, param) => figure_settings_changed.emit (param.name));
                _update_used_positions ();
                handle_style_change.begin ();
            }
        }

        private bool[] _used_positions;
        private Gee.AbstractList<Item> _items;
        private string[] _color_cycle;
        private string[] _used_colors;
        private GLib.Settings _settings;
        private bool _notify_selection_changed = true;

        public signal void style_changed (bool recolor_items);
        protected signal string load_request (File file, ProjectParseFlags parse_flags);
        protected signal bool add_history_state_request (double[] old_limits);

        // Clipboard signals
        protected signal void position_changed (uint index1, uint index2);
        protected signal void item_changed (Item item, string prop_name);
        protected signal void item_added (Item item);
        protected signal void item_removed (Item item, uint index);
        protected signal void figure_settings_changed (string prop);

        construct {
            this._items = new Gee.LinkedList<Item> ();
            this._color_cycle = {};
            items_changed.connect (_update_used_positions);
            this._settings = Application.get_settings_child ("figure");
            this.style_selection_model = new SingleSelection (StyleManager.style_model);
            this.figure_settings = new FigureSettings (_settings);

            var style_manager = StyleManager.instance;
            style_manager.style_changed.connect (stylename => {
                if (!figure_settings.use_custom_style) return;
                if (figure_settings.custom_style == stylename) {
                    handle_style_change.begin ();
                }
            });
            style_manager.style_deleted.connect (stylename => {
                if (!figure_settings.use_custom_style) return;
                if (figure_settings.custom_style == stylename) {
                    figure_settings.use_custom_style = false;
                }
            });
            style_manager.style_renamed.connect ((old_name, new_name) => {
                if (figure_settings.custom_style == old_name) {
                    figure_settings.custom_style = new_name;
                }
            });

            Adw.StyleManager.get_default().notify.connect (() => {
                if (!figure_settings.use_custom_style) {
                    handle_style_change.begin ();
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
            run_python_method ("_init_history_states");
            if (figure_settings.use_custom_style) {
                _on_custom_style.begin ();
            }
        }

        private void run_python_method (string method) {
            PythonHelper.run_method (this, method);
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

        public Item last () {
            return _items.last ();
        }

        // End section ListModel

        // Section SelectionModel
        // All required methods to implement the SelectionModel interface

        private void clear_selection () {
            foreach (Item item in _items) {
                item.selected = false;
            }
        }

        public Bitset get_selection_in_range (uint position, uint n_items) {
            var bitset = new Bitset.empty ();
            var range = _items[(int) position : (int) (position + n_items)];
            uint index = position;
            foreach (Item item in range) {
                if (item.selected) bitset.add (index);
                index++;
            }
            return bitset;
        }

        public bool is_selected (uint position) {
            return _items[(int) position].selected;
        }

        public bool select_all () {
            _notify_selection_changed = false;
            foreach (Item item in _items) {
                item.selected = true;
            }
            _notify_selection_changed = true;
            selection_changed.emit (0, _items.size);
            return true;
        }

        public bool select_item (uint position, bool unselect_rest) {
            if (unselect_rest) {
                _notify_selection_changed = false;
                clear_selection ();
                _items[(int) position].selected = true;
                _notify_selection_changed = true;
                selection_changed.emit (0, _items.size);
            } else {
                _items[(int) position].selected = true;
            }
            return true;
        }

        public bool select_range (uint position, uint n_items, bool unselect_rest) {
            var range = _items[(int) position : (int) (position + n_items)];
            _notify_selection_changed = false;
            if (unselect_rest) {
                clear_selection ();
                foreach (Item item in range) {
                    item.selected = true;
                }
                selection_changed.emit (0, _items.size);
            } else {
                foreach (Item item in range) {
                    item.selected = true;
                }
                selection_changed.emit (position, n_items);
            }
            _notify_selection_changed = true;
            return true;
        }

        public bool set_selection (Bitset selection, Bitset mask) {
            if (mask.is_empty ()) return true;
            _notify_selection_changed = false;
            uint index = 0;
            foreach (Item item in _items) {
                if (!mask.contains (index)) continue;
                item.selected = selection.contains (index);
                index++;
            }
            _notify_selection_changed = true;
            selection_changed.emit (0, _items.size);
            return true;
        }

        public bool unselect_all () {
            _notify_selection_changed = false;
            clear_selection ();
            _notify_selection_changed = true;
            selection_changed.emit (0, _items.size);
            return true;
        }

        public bool unselect_item (uint position) {
            _items[(int) position].selected = false;
            return true;
        }

        public bool unselect_range (uint position, uint n_items) {
            _notify_selection_changed = false;
            foreach (Item item in _items[(int) position : (int) (position + n_items)]) {
                item.selected = false;
            }
            _notify_selection_changed = true;
            selection_changed.emit (position, n_items);
            return true;
        }

        // End section SelectionModel

        // Section management

        public void clear () {
            uint n_items = get_n_items ();
            _items.clear ();
            items_changed.emit (0, n_items, 0);
            this.can_undo = false;
            this.can_redo = false;
            this.can_view_back = false;
            this.can_view_forward = false;
            this.figure_settings = new FigureSettings (_settings);
            run_python_method ("_init_history_states");
            this.file = null;
            this.unsaved = false;
            notify_property ("unsaved");
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
            item.notify["selected"].connect (() => {
                if (_notify_selection_changed) selection_changed.emit (index, 1);
            });
            item.notify.connect (_on_item_change);
            item.notify["xposition"].connect (_on_item_position_change);
            item.notify["yposition"].connect (_on_item_position_change);
            _items.insert (index, item);
            if (notify) items_changed.emit (index, 0, 1);
        }

        protected void _remove_item (uint index) {
            _items.remove_at ((int) index);
            items_changed.emit (index, 1, 0);
        }

        private bool is_default (string prop) {
            string figure_settings_value;
            figure_settings.get (prop, out figure_settings_value);
            return (figure_settings_value == _settings.get_string (prop));
        }

        private void append_used_color (string color) {
            if (color in _used_colors) return;
            if (!(color in _color_cycle)) return;
            _used_colors += color;
            if (_used_colors.length == _color_cycle.length) _used_colors = {};
        }

        public void add_items (Item[] items) {
            add_items_from_list (new Gee.ArrayList<Item>.wrap (items));
        }

        /**
         * Add items to be managed.
         *
         * Respects settings in regards to handling duplicate names.
         * New Items with a x- or y-label change the figures current labels if
         * they are still the default. If they are already modified and do not
         * match the items label, they get moved to another axis.
         */
        public void add_items_from_list (Gee.List<Item> items) {
            _used_colors = {};
            foreach (Item item in _items) {
                if (item.color in _color_cycle) append_used_color (item.color);
            }
            string[] used_names = get_names ();
            uint prev_size = get_n_items ();
            int original_position;
            foreach (Item item in items) {
                item.name = Tools.get_duplicate_string (item.name, used_names);
                used_names += item.name;
                if (item.color == "") {
                    foreach (string color in _color_cycle) {
                        if (!(color in _used_colors)) {
                            append_used_color (color);
                            item.color = color;
                            break;
                        }
                    }
                }
                if (item.xlabel != "") {
                    original_position = item.xposition;
                    if (original_position == 0) {
                        if (is_default ("bottom-label") | is_empty ()) {
                            figure_settings.bottom_label = item.xlabel;
                        } else if (item.xlabel != figure_settings.bottom_label) {
                            item.xposition = 1;
                        }
                    }
                    if (item.xposition == 1) {
                        if (is_default ("top-label")) {
                            figure_settings.top_label = item.xlabel;
                        } else if (item.xlabel != figure_settings.top_label) {
                            item.xposition = original_position;
                        }
                    }
                }
                if (item.ylabel != "") {
                    original_position = item.yposition;
                    if (original_position == 0) {
                        if (is_default ("left-label") | is_empty ()) {
                            figure_settings.left_label = item.ylabel;
                        } else if (item.ylabel != figure_settings.left_label) {
                            item.yposition = 1;
                        }
                    }
                    if (item.yposition == 1) {
                        if (is_default ("right-label")) {
                            figure_settings.right_label = item.ylabel;
                        } else if (item.ylabel != figure_settings.right_label) {
                            item.yposition = original_position;
                        }
                    }
                }
                _add_item (item, -1, false);
                item_added.emit (item);
            }
            items_changed.emit (prev_size, 0, items.size);
            optimize_limits ();
            add_history_state ();
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
            foreach (Item item in items) {
                uint index = this.index (item);
                item_removed.emit (item, index);
                _remove_item (index);
                int[] positions = { item.xposition, item.yposition + 2 };
                foreach (int position in positions) {
                    string direction = DIRECTION_NAMES[position];
                    string item_label = position < 2 ? item.xlabel : item.ylabel;
                    string axis_label;
                    figure_settings.get (direction + "_label", out axis_label);
                    if (_used_positions[position] && item_label == axis_label) {
                        string settings_value = _settings.get_string (direction + "-label");
                        figure_settings.set (direction + "_label", settings_value);
                    }
                }
            }
            add_history_state ();
        }

        // End section management

        // Section style

        private async void handle_style_change (bool recolor_items = false) {
            notify_property ("selected_stylename");
            run_python_method ("_update_selected_style");
            style_changed.emit (recolor_items);
        }

        protected Style get_selected_style () {
            return style_selection_model.get_selected_item () as Style;
        }

        protected void set_color_cycle (string[] color_cycle) {
            this._color_cycle = color_cycle;
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

        protected IteratorWrapper iterator_wrapper () {
            return new IteratorWrapper (_items.iterator ());
        }

        /**
         * There exists an issue with using the Gee.Iterator in python leading
         * to garbage data. Wrap the iterator in a class to circumvent this.
         */
        public class IteratorWrapper : Object {
            private Iterator<Item> iterator;

            public IteratorWrapper (Iterator<Item> iterator) {
                this.iterator = iterator;
            }

            public Item? next () {
                if (!iterator.has_next ()) return null;
                iterator.next ();
                return iterator.get ();
            }
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
            run_python_method ("_optimize_limits");
            add_view_history_state ();
        }

        // End section misc

        // Section history

        public void add_history_state (double[]? old_limits = null) {
            if (!add_history_state_request.emit (old_limits)) return;
            this.can_undo = true;
            this.can_redo = false;
            this.unsaved = true;
            notify_property ("unsaved");
        }

        public void undo () {
            run_python_method ("_undo");
            add_view_history_state ();
        }

        public void redo () {
            run_python_method ("_redo");
            add_view_history_state ();
        }

        public void add_view_history_state () {
            run_python_method ("_add_view_history_state");
            this.can_view_back = true;
            this.can_view_forward = false;
            this.unsaved = true;
            notify_property ("unsaved");
        }

        public void view_back () {
            run_python_method ("_view_back");
        }

        public void view_forward () {
            run_python_method ("_view_forward");
        }

        // End section history

        // Section save & load

        public void save () {
            run_python_method ("_save");
            this.unsaved = false;
            notify_property ("unsaved");
        }

        public void load (File file, ProjectParseFlags flags = ProjectParseFlags.NONE) throws ProjectParseError {
            string error = load_request.emit (file, flags);
            if (error == "") {
                this.file = file;
                this.unsaved = false;
                notify_property ("unsaved");
            } else {
                switch (error) {
                    case "LEGACY_MIGRATION_DISALLOWED":
                        throw new ProjectParseError.LEGACY_MIGRATION_DISALLOWED ("");
                    case "BETA_DISALLOWED":
                        throw new ProjectParseError.BETA_DISALLOWED ("");
                    default:
                        throw new ProjectParseError.INVALID_PROJECT (error);
                }
            }
        }

        // End section save & load

        // Section listeners

        private void _on_item_change (Object item, ParamSpec spec) {
            item_changed.emit ((Item) item, spec.name);
        }

        private void _on_item_position_change () {
            optimize_limits ();
            _update_used_positions ();
            items_changed.emit (0, 0, 0);
        }

        private async void _on_use_custom_style () {
            if (figure_settings.use_custom_style) {
                yield _on_custom_style ();
            } else {
                style_selection_model.set_selected (0);
                yield handle_style_change (true);
            }
        }

        private async void _on_custom_style () {
            if (!figure_settings.use_custom_style) return;
            var style_model = style_selection_model.get_model ();
            for (uint i = 1; i < style_model.get_n_items (); i++) {
                Style style = style_model.get_item (i) as Style;
                if (style.name == figure_settings.custom_style) {
                    style_selection_model.set_selected (i);
                    break;
                }
            }
            yield handle_style_change (true);
        }

        // End section listeners
    }
}
