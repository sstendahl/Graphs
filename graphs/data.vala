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
        public bool can_view_back { get; private set; default = false; }
        public bool can_view_forward { get; private set; default = false; }
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
        private Item[] _items = new Item[8];
        private int _n_items = 0;
        private string[] _color_cycle;
        private string[] _used_colors;
        private string[] _errbar_color_cycle;
        private string[] _used_errbar_colors;
        private GLib.Settings _settings;
        private bool _notify_selection_changed = true;
        private Gee.List<Limits> _view_history_states = new ArrayList<Limits> ();
        private int _view_history_pos = -1;

        public signal void style_changed (bool recolor_items);
        protected signal string load_request (File file, ProjectParseFlags parse_flags);
        protected signal bool add_history_state_request ();

        // Clipboard signals
        protected signal void position_changed (uint index1, uint index2);
        protected signal void item_changed (Item item, string prop_name);
        protected signal void item_added (Item item);
        protected signal void item_removed (Item item, uint index);
        protected signal void figure_settings_changed (string prop);

        construct {
            this._color_cycle = {};
            this._errbar_color_cycle = {};
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

            Adw.StyleManager.get_default ().notify.connect (() => {
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
            _view_history_states.add (figure_settings.get_limits ());
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
            return _n_items;
        }

        public Item last () {
            return _items[_n_items - 1];
        }

        // End section ListModel

        // Section SelectionModel
        // All required methods to implement the SelectionModel interface

        private void clear_selection () {
            for (uint index = 0; index < _n_items; index++) {
                _items[index].selected = false;
            }
        }

        public Bitset get_selection_in_range (uint position, uint n_items) {
            var bitset = new Bitset.empty ();
            for (uint index = position; index < position + n_items; index++) {
                if (_items[index].selected) bitset.add (index);
            }
            return bitset;
        }

        public bool is_selected (uint position) {
            return _items[position].selected;
        }

        public bool select_all () {
            _notify_selection_changed = false;
            for (uint index = 0; index < _n_items; index++) {
                _items[index].selected = true;
            }
            _notify_selection_changed = true;
            selection_changed.emit (0, _n_items);
            return true;
        }

        public bool select_item (uint position, bool unselect_rest) {
            if (unselect_rest) {
                _notify_selection_changed = false;
                clear_selection ();
                _items[position].selected = true;
                _notify_selection_changed = true;
                selection_changed.emit (0, _n_items);
            } else {
                _items[position].selected = true;
            }
            return true;
        }

        public bool select_range (uint position, uint n_items, bool unselect_rest) {
            _notify_selection_changed = false;
            if (unselect_rest) {
                clear_selection ();
                for (uint index = position; index < position + n_items; index++) {
                    _items[index].selected = true;
                }
                selection_changed.emit (0, _n_items);
            } else {
                for (uint index = position; index < position + n_items; index++) {
                     _items[index].selected = true;
                }
                selection_changed.emit (position, n_items);
            }
            _notify_selection_changed = true;
            return true;
        }

        public bool set_selection (Bitset selection, Bitset mask) {
            if (mask.is_empty ()) return true;
            _notify_selection_changed = false;
            for (int index = 0; index < _n_items; index++) {
                if (!mask.contains (index)) continue;
                _items[index].selected = selection.contains (index);
            }
            _notify_selection_changed = true;
            selection_changed.emit (0, _n_items);
            return true;
        }

        public bool unselect_all () {
            _notify_selection_changed = false;
            clear_selection ();
            _notify_selection_changed = true;
            selection_changed.emit (0, _n_items);
            return true;
        }

        public bool unselect_item (uint position) {
            _items[position].selected = false;
            return true;
        }

        public bool unselect_range (uint position, uint n_items) {
            _notify_selection_changed = false;
            for (uint index = position; index < position + n_items; index++) {
                _items[index].selected = false;
            }
            _notify_selection_changed = true;
            selection_changed.emit (position, n_items);
            return true;
        }

        // End section SelectionModel

        // Section management

        public void clear () {
            uint n_items = get_n_items ();
            for (int index = 0; index < n_items; index++) {
                _items[index] = null;
            }
            _n_items = 0;
            items_changed.emit (0, n_items, 0);
            this.can_undo = false;
            this.can_redo = false;
            this.can_view_back = false;
            this.can_view_forward = false;
            this.figure_settings = new FigureSettings (_settings);
            _view_history_states.clear ();
            _view_history_states.add (figure_settings.get_limits ());
            run_python_method ("_init_history_states");
            this.file = null;
            this.unsaved = false;
            notify_property ("unsaved");
        }

        private void grow_if_needed (int grow_size) {
            int minimum_size = _n_items + grow_size;
            if (minimum_size > _items.length) {
                // double the capacity unless we add even more items at this time
                _items.resize (grow_size > _items.length ? minimum_size : 2 * _items.length);
            }
        }

        protected void _update_used_positions () {
            if (_n_items == 0) {
                _used_positions = {true, false, true, false};
                return;
            }
            bool[] used_positions = {false, false, false, false};
            Item item;
            for (uint index = 0; index < _n_items; index++) {
                item = _items[index];
                if (figure_settings.hide_unselected && !item.selected) continue;
                used_positions[item.xposition] = true;
                used_positions[item.yposition + 2] = true;
            }
            _used_positions = used_positions;
        }

        private void _connect_to_item (Item item) {
            item.notify["selected"].connect (() => {
                if (_notify_selection_changed) selection_changed.emit (index (item), 1);
            });
            item.notify.connect (_on_item_change);
            item.notify["xposition"].connect (_on_item_position_change);
            item.notify["yposition"].connect (_on_item_position_change);
        }

        protected void _add_item (Item item) {
            _connect_to_item (item);
            grow_if_needed (1);
            _items[_n_items] = item;
            items_changed.emit (_n_items++, 0, 1);
        }

        protected void _insert_item (Item item, int index) {
            _connect_to_item (item);
            grow_if_needed (1);
            _items.move (index, index + 1, _n_items - index);
            _items[index] = item;
            _n_items++;
            items_changed.emit (index, 0, 1);
        }

        protected void _remove_item (uint index) {
            _items[index] = null;
            _items.move ((int) index + 1, (int) index, (int) (_n_items - index - 1));
            _n_items--;
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

        private void append_used_errbar_color (string color) {
            if (color in _used_errbar_colors) return;
            if (!(color in _errbar_color_cycle)) return;
            _used_errbar_colors += color;
            if (_used_errbar_colors.length == _errbar_color_cycle.length) _used_errbar_colors = {};
        }

        /**
         * Add items to be managed.
         *
         * Respects settings in regards to handling duplicate names.
         * New Items with a x- or y-label change the figures current labels if
         * they are still the default. If they are already modified and do not
         * match the items label, they get moved to another axis.
         */
        public void add_items (Item[] items) {
            _used_colors = {};
            _used_errbar_colors = {};
            foreach (Item item in this) {
                if (item.color in _color_cycle) append_used_color (item.color);
                if (item is DataItem) {
                    string errcolor = ((DataItem) item).errcolor;
                    if (errcolor in _errbar_color_cycle) append_used_errbar_color (errcolor);
                }
            }
            string[] used_names = get_names ();
            uint prev_size = _n_items;
            grow_if_needed (items.length);
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
                if (item is DataItem) {
                    string errcolor = ((DataItem) item).errcolor;
                    if (errcolor == "") {
                        foreach (string color in _errbar_color_cycle) {
                            if (!(color in _used_errbar_colors)) {
                                append_used_errbar_color (color);
                                item.set ("errcolor", color);
                                break;
                            }
                        }
                    }
                }
                if (item.xlabel != "") {
                    var original_position = item.xposition;
                    if (original_position == XPosition.BOTTOM) {
                        if (is_default ("bottom-label") | is_empty ()) {
                            figure_settings.bottom_label = item.xlabel;
                        } else if (item.xlabel != figure_settings.bottom_label) {
                            item.xposition = XPosition.TOP;
                        }
                    }
                    if (item.xposition == XPosition.TOP) {
                        if (is_default ("top-label")) {
                            figure_settings.top_label = item.xlabel;
                        } else if (item.xlabel != figure_settings.top_label) {
                            item.xposition = original_position;
                        }
                    }
                }
                if (item.ylabel != "") {
                    var original_position = item.yposition;
                    if (original_position == YPosition.LEFT) {
                        if (is_default ("left-label") | is_empty ()) {
                            figure_settings.left_label = item.ylabel;
                        } else if (item.ylabel != figure_settings.left_label) {
                            item.yposition = YPosition.RIGHT;
                        }
                    }
                    if (item.yposition == YPosition.RIGHT) {
                        if (is_default ("right-label")) {
                            figure_settings.right_label = item.ylabel;
                        } else if (item.ylabel != figure_settings.right_label) {
                            item.yposition = original_position;
                        }
                    }
                }
                _connect_to_item (item);
                _items[_n_items++] = item;
                item_added.emit (item);
            }
            items_changed.emit (prev_size, 0, items.length);
            optimize_limits ();
            add_history_state ();
        }

        public void set_items (Item[] items) {
            uint removed = _n_items;
            foreach (Item item in items) {
                _connect_to_item (item);
            }
            _items = items;
            _n_items = items.length;
            _update_used_positions ();
            items_changed.emit (0, removed, _n_items);
        }

        public void delete_items (Item[] items) {
            foreach (Item item in items) {
                uint index = this.index (item);
                item_removed.emit (item, index);
                _remove_item (index);

                string axis_label;
                string prop;

                prop = item.xposition.friendly_string () + "-label";
                figure_settings.get (prop, out axis_label);
                if (_used_positions[item.xposition] && item.xlabel == axis_label) {
                    figure_settings.set (prop, _settings.get_string (prop));
                }

                prop = item.yposition.friendly_string () + "-label";
                figure_settings.get (prop, out axis_label);
                if (_used_positions[item.yposition + 2] && item.ylabel == axis_label) {
                    figure_settings.set (prop, _settings.get_string (prop));
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
            return (Style) style_selection_model.get_selected_item ();
        }

        protected void set_color_cycle (string[] color_cycle) {
            this._color_cycle = color_cycle;
        }

        protected void set_errbar_color_cycle (string[] color_cycle) {
            this._errbar_color_cycle = color_cycle;
        }

        // End section style

        // Section Vala iterator

        public Iterator<Item> iterator () {
            return new ItemIterator (this);
        }

        private class ItemIterator : Object, Traversable<Item>, Iterator<Item> {
            private Data _data;
            private int _index = -1;

            public bool read_only { get; default = true; }
            public bool valid { get { return _index >= 0 && has_next (); } }

            public ItemIterator (Data data) {
                _data = data;
            }

            public bool @foreach (ForallFunc<Item> f) {
                uint n_items = _data.get_n_items ();
                while (_index < n_items) {
                    if (!f ((Item) _data.get_item (_index))) return false;
                    _index++;
                }
                _index--;
                return true;
            }

            public bool has_next () {
                return _index + 1 < _data.get_n_items ();
            }

            public bool next () {
                if (has_next ()) {
                    _index++;
                    return true;
                }
                return false;
            }

            public new Item get () {
                return (Item) _data.get_item (_index);
            }

            public void remove () {
                assert_not_reached ();
            }
        }

        public bool @foreach (ForallFunc<Item> f) {
            for (int i = 0; i < _n_items; i++) {
                if (!f (_items[i])) return false;
            }
            return true;
        }

        // End section Vala iterator

        // Section misc

        protected string get_version () {
            return Config.VERSION;
        }

        public bool is_empty () {
            return _n_items == 0;
        }

        public Item[] get_items () {
            return _items[:_n_items];
        }

        public string[] get_names () {
            string[] names = new string[_n_items];
            for (int index = 0; index < _n_items; index++) {
                names[index] = _items[index].name;
            }
            return names;
        }

        public uint index (Item item) {
            for (uint index = 0; index < _n_items; index++) {
                if (_items[index] == item) return index;
            }
            assert_not_reached ();
        }

        public bool[] get_used_positions () {
            return _used_positions;
        }

        public void change_position (uint index1, uint index2) {
            if (index1 == index2) return;
            Item item = _items[index2];
            if (index1 < index2) {
                _items.move ((int) index1, (int) index1 + 1, (int) (index2 - index1));
            } else {
                _items.move ((int) index2 + 1, (int) index2, (int) (index1 - index2));
            }
            _items[index1] = item;
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

        public void add_history_state () {
            if (!add_history_state_request.emit ()) return;
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
            var limits = figure_settings.get_limits ();
            var last = _view_history_states.last ();
            if (MathTools.all_close (limits.values (), last.values ())) return;

            if (_view_history_pos != -1) {
                int new_size = _view_history_states.size + _view_history_pos + 1;
                while (_view_history_states.size > new_size) {
                    _view_history_states.remove_at (_view_history_states.size - 1);
                }
            }

            if (_view_history_states.size > 101) {
                _view_history_states.remove_at (0);
            }

            _view_history_pos = -1;
            _view_history_states.add (limits);

            this.can_view_back = true;
            this.can_view_forward = false;
            this.unsaved = true;
            notify_property ("unsaved");
        }

        public void view_back () {
            if (!can_view_back) return;
            int index = _view_history_states.size + --_view_history_pos;
            figure_settings.set_limits (_view_history_states.get (index));

            this.can_view_back = _view_history_pos.abs () < _view_history_states.size;
            this.can_view_forward = true;
        }

        public void view_forward () {
            if (!can_view_forward) return;
            int index = _view_history_states.size + ++_view_history_pos;
            figure_settings.set_limits (_view_history_states.get (index));

            this.can_view_back = true;
            this.can_view_forward = _view_history_pos < -1;
        }

        protected int get_view_history (out Limits[] history) {
            history = _view_history_states.to_array ();
            return _view_history_pos;
        }

        protected void set_view_history (int pos, Limits[] history) {
            _view_history_states = new ArrayList<Limits>.wrap (history);
            _view_history_pos = pos;

            this.can_view_back = _view_history_pos.abs () < _view_history_states.size;
            this.can_view_forward = _view_history_pos < -1;
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
                Style style = (Style) style_model.get_item (i);
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
