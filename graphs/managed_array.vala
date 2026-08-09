// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * A simple and lightweight managed array.
     * Nut usable with primitive types.
     */
    public class ManagedArray<T> {
        public T[] data;
        public int length = 0;

        public ManagedArray (int len = 8) {
            this.data = new T[len];
        }

        public ManagedArray.take (owned T[] data) {
            this.length = data.length;
            this.data = (owned) data;
        }

        private void grow_if_needed (int grow_size) {
            int minimum_size = length + grow_size;
            int capacity = data.length;
            if (minimum_size > capacity) {
                // double the capacity unless we add even more items at this time
                data.resize (grow_size > capacity ? minimum_size : 2 * capacity);
            }
        }

        public void @set (int i, T t) {
            data[i] = t;
        }

        public T @get (int i) {
            return data[i];
        }

        public int index (T t) {
            for (int index = 0; index < length; index++) {
                if (data[index] == t) return index;
            }
            return -1;
        }

        public void append (T t) {
            grow_if_needed (1);
            data[length++] = t;
        }

        public void append_all (T[] t_array) {
            grow_if_needed (t_array.length);
            foreach (T t in t_array) {
                data[length++] = t;
            }
        }

        public void insert (T t, int i) {
            grow_if_needed (1);
            data.move (i, i + 1, length - i);
            data[i] = t;
            length++;
        }

        public void remove_at (int i) {
            data[i] = null;
            data.move (i + 1, i, length - i - 1);
            length--;
        }

        public unowned T[] peek () {
            return data[:length];
        }

        public T[] steal () {
            data.resize (length);
            return (owned) data;
        }

        public void @foreach (Func<T> func) {
            for (int i = 0; i < length; i++) {
                func (data[i]);
            }
        }

        public Iterator<T> iterator () {
            return new Iterator<T> (this);
        }
    }

    public class Iterator<T> {
        private unowned ManagedArray<T> _data;
        private int _index = -1;

        public Iterator (ManagedArray<T> data) {
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
