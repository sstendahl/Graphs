// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public abstract class Item : Object {
        public string typename { get; construct set; }
        public string name { get; set; default = ""; }
        public string color { get; set; default = ""; }
        public float alpha { get; set; default = 1; }
        public bool selected { get; set; default = true; }
        public bool visible { get; set; default = true; }
        public string xlabel { get; set; default = ""; }
        public string ylabel { get; set; default = ""; }
        public XPosition xposition { get; set; default = XPosition.BOTTOM; }
        public YPosition yposition { get; set; default = YPosition.LEFT; }

        public Gdk.RGBA get_rgba () {
            Gdk.RGBA rgba = Tools.hex_to_rgba (color);
            rgba.alpha = alpha;
            return rgba;
        }

        public void set_rgba (Gdk.RGBA rgba) {
            this.color = Tools.rgba_to_hex (rgba);
            this.alpha = rgba.alpha;
        }

        private GenericSet<unowned Item>? _dependents = null;

        public void register_dependent (Item dependent) {
            if (_dependents == null) {
                _dependents = new GenericSet<unowned Item> (
                    direct_hash, direct_equal
                );
            }
            _dependents.add (dependent);
        }

        public void unregister_dependent (Item dependent) {
            if (_dependents != null) _dependents.remove (dependent);
        }

        public Item[] get_dependents () {
            if (_dependents == null) return new Item[0];
            uint length = _dependents.length;
            var dependents = new Item[length];
            var iter = _dependents.iterator ();
            for (int i = 0; i < length; i++) {
                dependents[i] = iter.next_value ();
            }
            return (owned) dependents;
        }
    }

    public interface LegendableItem : Item {
        public abstract bool legend { get; set; }
    }

    public interface EquationBasedItem : Item {
        public abstract Ast equation { get; set; }
    }
}
