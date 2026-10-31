// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public enum XPosition {
        BOTTOM,
        TOP;

        public unowned string friendly_string () {
            EnumClass enumc = (EnumClass) typeof (XPosition).class_ref ();
            unowned EnumValue? eval = enumc.get_value (this);
            return eval.value_nick;
        }
    }

    public enum YPosition {
        LEFT,
        RIGHT;

        public unowned string friendly_string () {
            EnumClass enumc = (EnumClass) typeof (YPosition).class_ref ();
            unowned EnumValue? eval = enumc.get_value (this);
            return eval.value_nick;
        }
    }

    protected delegate Value StylePropertyTransform (StyleData s);

    protected struct StylePropertyBinding {
        string prop;
        StylePropertyTransform transform;
    }

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

        protected virtual unowned StylePropertyBinding[]? get_property_bindings () {
            return null;
        }

        public void override (StyleParameters style) {
            unowned var bindings = get_property_bindings ();
            if (bindings == null) return;

            unowned StyleData data = style.data;
            foreach (unowned var binding in bindings) {
                Value val = binding.transform (data);
                set_property (binding.prop, val);
            }
        }

        public void reset (StyleParameters old_style, StyleParameters new_style) {
            unowned var bindings = get_property_bindings ();
            if (bindings == null) return;

            unowned var object_class = get_class ();
            unowned StyleData old_data = old_style.data;
            unowned StyleData new_data = new_style.data;
            foreach (unowned var binding in bindings) {
                ParamSpec pspec = object_class.find_property (binding.prop);

                Value old_val = binding.transform (old_data);
                Value current_val = Value (pspec.value_type);
                get_property (binding.prop, ref current_val);

                if (pspec.values_cmp (old_val, current_val) != 0) continue;

                Value new_val = binding.transform (new_data);
                set_property (binding.prop, new_val);
            }
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
