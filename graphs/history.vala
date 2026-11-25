// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public enum ChangeType {
        ITEM_PROPERTY_CHANGED,
        ITEM_ADDED,
        ITEM_REMOVED,
        ITEMS_SWAPPED,
        FIGURE_SETTINGS_CHANGED
    }

    public class DataHistoryState {
        public Limits limits;
        public DataHistoryChange[] changes;

        public DataHistoryState (Limits limits, owned DataHistoryChange[] changes) {
            this.limits = limits;
            this.changes = (owned) changes;
        }
    }

    public class DataHistoryChange {
    }

    public class DataHistoryPropertyChange : DataHistoryChange {
        private uint _index;
        private string _prop;
        private Variant _old_value;
        private Variant _new_value;

        public DataHistoryPropertyChange (uint index, owned string prop, owned Variant old_value, owned Variant new_value) {
            this._index = index;
            this._prop = (owned) prop;
            this._old_value = (owned) old_value;
            this._new_value = (owned) new_value;
        }

        public uint index () {
            return _index;
        }

        public unowned string prop () {
            return _prop;
        }

        public unowned Variant old_value () {
            return _old_value;
        }

        public unowned Variant new_value () {
            return _new_value;
        }
    }

    public class DataHistoryItemAdded : DataHistoryChange {
        private Variant _item;

        public DataHistoryItemAdded (owned Variant item) {
            this._item = (owned) item;
        }

        public unowned Variant item () {
            return _item;
        }
    }

    public class DataHistoryItemRemoved : DataHistoryChange {
        private Variant _item;
        private uint _index;

        public DataHistoryItemRemoved (owned Variant item, uint index) {
            this._item = (owned) item;
            this._index = index;
        }

        public unowned Variant item () {
            return _item;
        }

        public uint index () {
            return _index;
        }
    }

    public class DataHistoryItemsSwapped : DataHistoryChange {
        private uint _index1;
        private uint _index2;

        public DataHistoryItemsSwapped (uint index1, uint index2) {
            this._index1 = index1;
            this._index2 = index2;
        }

        public uint index1 () {
            return _index1;
        }

        public uint index2 () {
            return _index2;
        }
    }

    public class DataHistoryFigureSettingsChange : DataHistoryChange {
        private string _prop;
        private Variant _old_value;
        private Variant _new_value;

        public DataHistoryFigureSettingsChange (owned string prop, owned Variant old_value, owned Variant new_value) {
            this._prop = (owned) prop;
            this._old_value = (owned) old_value;
            this._new_value = (owned) new_value;
        }

        public unowned string prop () {
            return _prop;
        }

        public unowned Variant old_value () {
            return _old_value;
        }

        public unowned Variant new_value () {
            return _new_value;
        }
    }
}
