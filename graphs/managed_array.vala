// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * A simple and lightweight managed array.
     * Not usable with primitive types.
     */
    public class ManagedArray<T> {
        private T[] _data;
        private int _length;

        public int length { get { return _length; } }

        public ManagedArray (int len = 8) {
            this._length = 0;
            this._data = new T[len];
        }

        public ManagedArray.take (owned T[] data) {
            this._length = data.length;
            this._data = (owned) data;
        }

        private void grow_if_needed (int grow_size) {
            int minimum_size = _length + grow_size;
            int capacity = _data.length;
            if (minimum_size > capacity) {
                // double the capacity unless we add even more items at this time
                _data.resize (grow_size > capacity ? minimum_size : 2 * capacity);
            }
        }

        public void @set (int i, T t) requires (i >= 0 && i < _length) {
            _data[i] = t;
        }

        public T @get (int i) {
            return _data[i];
        }

        public int index (T t) {
            for (int index = 0; index < _length; index++) {
                if (_data[index] == t) return index;
            }
            return -1;
        }

        public void append (T t) {
            grow_if_needed (1);
            _data[_length++] = t;
        }

        public void append_all (T[] t_array) {
            grow_if_needed (t_array.length);
            foreach (T t in t_array) {
                _data[_length++] = t;
            }
        }

        public void insert (int i, T t) {
            grow_if_needed (1);
            _data.move (i, i + 1, length - i);
            _data[i] = t;
            _length++;
        }

        public void remove_at (int i) {
            _data[i] = null;
            _data.move (i + 1, i, length - i - 1);
            _length--;
        }

        public void move_to (int i1, int i2) {
            T t = _data[i2];
            if (i1 < i2) {
                _data.move (i1, i1 + 1, i2 - i1);
            } else {
                _data.move (i2 + 1, i2, i1 - i2);
            }
            _data[i1] = t;
        }

        public unowned T[] peek () {
            return _data[:length];
        }

        public T[] steal () {
            _data.resize (length);
            return (owned) _data;
        }

        public void @foreach (Func<T> func) {
            for (int i = 0; i < _length; i++) {
                func (_data[i]);
            }
        }

        public ManagedArrayIterator<T> iterator () {
            return new ManagedArrayIterator<T> (this);
        }
    }

    public class ManagedArrayIterator<T> {
        private unowned ManagedArray<T> _data;
        private int _index = -1;

        public ManagedArrayIterator (ManagedArray<T> data) {
            _data = data;
        }

        public bool has_next () {
            return _index + 1 < _data.length;
        }

        public bool next () {
            if (has_next ()) {
                _index++;
                return true;
            }
            return false;
        }

        public new T @get () {
            return _data[_index];
        }
    }
}
