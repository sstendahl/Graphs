// SPDX-License-Identifier: GPL-3.0-or-later
using Gdk;

namespace Graphs {
    /**
     * Small list class
     */
    public class ItemList : Object {
        private Gee.List<Item> _items = new Gee.ArrayList<Item> ();

        public void add (Item item) {
            _items.add (item);
        }

        public void add_all (Item[] items) {
            foreach (Item item in items) {
                _items.add (item);
            }
        }

        public Item[] to_array () {
            return _items.to_array ();
        }
    }

    protected delegate Value StyleTransformFunc (Value val);

    protected struct StyleBinding {
        string property;
        string key;
        unowned StyleTransformFunc transform;
    }

    /**
     * Base item class
     */
    public abstract class Item : Object {
        public string typename { get; construct set; }
        public string name { get; set; default = ""; }
        public string color { get; set; default = ""; }
        public float alpha { get; set; default = 1; }
        public bool selected { get; set; default = true; }
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

        protected virtual unowned StyleBinding[]? get_style_bindings () {
            return null;
        }

        public void reset (StyleParameters old_style, StyleParameters new_style) {
            unowned var style_bindings = get_style_bindings ();
            if (style_bindings == null) return;

            foreach (unowned StyleBinding binding in style_bindings) {
                Value old_val = old_style.get_param (binding.key);
                Value new_val = new_style.get_param (binding.key);

                if (binding.transform != null) {
                    old_val = binding.transform (old_val);
                    new_val = binding.transform (new_val);
                }

                var klass = (ObjectClass) get_type ().class_ref ();
                var pspec = klass.find_property (binding.property);
                if (pspec.values_cmp (old_val, new_val) != 0)
                    set_property (binding.property, new_val);
            }
        }

        public void override (StyleParameters style) {
            unowned var style_bindings = get_style_bindings ();
            if (style_bindings == null) return;

            foreach (unowned StyleBinding binding in style_bindings) {
                Value val = style.get_param (binding.key);

                if (binding.transform != null)
                    val = binding.transform (val);

                set_property (binding.property, val);
            }
        }
    }

    public interface EquationBasedItem : Item {
        public abstract Ast equation { get; set; }
    }

    public class DataHolder : Object {
        private double[] _xdata;
        private double[] _ydata;
        private double[]? _xerr;
        private double[]? _yerr;

        public DataHolder (owned double[] xdata, owned double[] ydata, owned double[]? xerr, owned double[]? yerr) {
            _xdata = (owned) xdata;
            _ydata = (owned) ydata;
            _xerr = (owned) xerr;
            _yerr = (owned) yerr;
        }

        public DataHolder.empty () {
            _xdata = new double[0];
            _ydata = new double[0];
            _xerr = null;
            _yerr = null;
        }

        public unowned double[] get_xdata () {
            return _xdata;
        }

        public unowned double[] get_ydata () {
            return _ydata;
        }

        public unowned double[]? get_xerr () {
            return _xerr;
        }

        public unowned double[]? get_yerr () {
            return _yerr;
        }

        public GLib.Bytes get_xdata_b () {
            return new Bytes ((uint8[]) _xdata);
        }

        public GLib.Bytes get_ydata_b () {
            return new Bytes ((uint8[]) _ydata);
        }

        public GLib.Bytes? get_xerr_b () {
            return _xerr == null ? null : new Bytes ((uint8[]) _xerr);
        }

        public GLib.Bytes? get_yerr_b () {
            return _yerr == null ? null : new Bytes ((uint8[]) _yerr);
        }
    }

    public class DataItem : Item {
        public DataHolder data { get; set; default = new DataHolder.empty (); }
        public bool errbarsabove { get; set; default = false; }
        public double errcapsize { get; set; default = 0; }
        public double errcapthick { get; set; default = 1; }
        public string errcolor { get; set; default = ""; }
        public double errlinewidth { get; set; default = 1; }
        public Linestyle linestyle { get; set; default = Linestyle.SOLID; }
        public double linewidth { get; set; default = 3; }
        public Markerstyle markerstyle { get; set; default = Markerstyle.NONE; }
        public double markersize { get; set; default = 7; }
        public bool showxerr { get; set; default = true; }
        public bool showyerr { get; set; default = true; }

        private static Value linestyle_transform (Value val) {
            return Linestyle.from_string ((string) val);
        }

        private static Value markerstyle_transform (Value val) {
            return Markerstyle.from_style ((string) val);
        }

        private const StyleBinding[] STYLE_BINDINGS = {
            { "errbarsabove", "errorbar.barsabove", null },
            { "errcapsize", "errorbar.capsize", null },
            { "errcapthick", "errorbar.capthick", null },
            { "errlinewidth", "errorbar.linewidth", null },
            { "linestyle", "lines.linestyle", linestyle_transform },
            { "linewidth", "lines.linewidth", null },
            { "markerstyle", "lines.marker", markerstyle_transform },
            { "markersize", "lines.markersize", null },
        };

        protected override unowned StyleBinding[]? get_style_bindings () {
            return STYLE_BINDINGS;
        }

        construct {
            typename = _("Dataset");
        }

        public DataItem (StyleParameters parameters, owned double[] xdata, owned double[] ydata, owned double[]? xerr = null, owned double[]? yerr = null) {
            Object (data: new DataHolder ((owned) xdata, (owned) ydata, (owned) xerr, (owned) yerr));
            override (parameters);
        }

        public unowned double[] get_xdata () {
            return data.get_xdata ();
        }

        public unowned double[] get_ydata () {
            return data.get_ydata ();
        }

        public bool has_xerr () {
            return data.get_xerr () != null;
        }

        public bool has_yerr () {
            return data.get_yerr () != null;
        }
    }

    public class GeneratedDataItem : DataItem, EquationBasedItem {
        public string xstart { get; set; default = "0"; }
        public string xstop { get; set; default = "10"; }
        public int steps { get; set; default = 100; }
        public Scale scale { get; set; default = Scale.LINEAR; }

        private Ast _equation;
        public Ast equation {
            get { return _equation; }
            set {
                try {
                    if (_equation != null && "Y = " + ast_to_expression (_equation) == name)
                        name = "Y = " + ast_to_expression (value);

                    _equation = value;
                } catch (MathError e) { assert_not_reached (); }

                regenerate ();
            }
        }

        construct {
            typename = _("Generated Dataset");

            const string[] PROPS = {"xstart", "xstop", "steps", "scale"};
            foreach (string prop in PROPS) {
                this.notify[prop].connect (regenerate);
            }
        }

        public GeneratedDataItem (StyleParameters parameters, Ast equation, string xstart, string xstop, int steps, Scale scale) {
            Object (
                equation: equation,
                xstart: xstart,
                xstop: xstop,
                steps: steps,
                scale: scale
            );
            override (parameters);
        }

        private void regenerate () {
            try {
                data = MathTools.equation_to_data (
                    _equation,
                    evaluate_string (xstart),
                    evaluate_string (xstop),
                    steps, scale);
            } catch (MathError e) { assert_not_reached (); }
        }
    }

    public class EquationItem : Item, EquationBasedItem {
        public EquationLinestyle linestyle { get; set; default = EquationLinestyle.SOLID; }
        public double linewidth { get; set; default = 3; }

        private Ast _equation;
        public Ast equation {
            get { return _equation; }
            set {
                try {
                    if (_equation != null && "Y = " + ast_to_expression (_equation) == name)
                        name = "Y = " + ast_to_expression (value);

                    _equation = value;
                } catch (MathError e) { assert_not_reached (); }
            }
        }

        private static Value linestyle_transform (Value val) {
            return EquationLinestyle.from_string ((string) val);
        }

        private const StyleBinding[] STYLE_BINDINGS = {
            { "linestyle", "lines.linestyle", linestyle_transform },
            { "linewidth", "lines.linewidth", null },
        };

        protected override unowned StyleBinding[]? get_style_bindings () {
            return STYLE_BINDINGS;
        }

        construct {
            typename = _("Equation");
        }

        public EquationItem (StyleParameters parameters, Ast equation) {
            Object (equation: equation);
            override (parameters);
        }
    }

    public class TextItem : Item {
        public double xanchor { get; set; default = 0; }
        public double yanchor { get; set; default = 0; }
        public string text { get; set; default = ""; }
        public double size { get; set; default = 12; }
        public int rotation { get; set; default = 0; }

        private const StyleBinding[] STYLE_BINDINGS = {
            { "size", "font.size", null },
            { "color", "text.color", null },
        };

        protected override unowned StyleBinding[]? get_style_bindings () {
            return STYLE_BINDINGS;
        }

        construct {
            typename = _("Label");
        }

        public TextItem (StyleParameters parameters, double xanchor, double yanchor, string text) {
            Object (
                xanchor: xanchor,
                yanchor: yanchor,
                text: text
            );
            override (parameters);
        }
    }

    public class FillHolder : Object {
        private double[] _xdata;
        private double[] _lower;
        private double[] _upper;

        public FillHolder (owned double[] xdata, owned double[] lower, owned double[] upper) {
            _xdata = (owned) xdata;
            _lower = (owned) lower;
            _upper = (owned) upper;
        }

        public FillHolder.empty () {
            _xdata = new double[0];
            _lower = new double[0];
            _upper = new double[0];
        }

        public unowned double[] get_xdata () {
            return _xdata;
        }

        public unowned double[] get_lower () {
            return _lower;
        }

        public unowned double[] get_upper () {
            return _upper;
        }

        public GLib.Bytes get_xdata_b () {
            return new Bytes ((uint8[]) _xdata);
        }

        public GLib.Bytes get_lower_b () {
            return new Bytes ((uint8[]) _lower);
        }

        public GLib.Bytes get_upper_b () {
            return new Bytes ((uint8[]) _upper);
        }
    }

    public class FillItem : Item {
        public FillHolder data { get; set; default = new FillHolder.empty (); }

        construct {
            typename = _("Fill");
        }

        public FillItem (StyleParameters parameters, owned double[] xdata, owned double[] lower, owned double[] upper) {
            Object (data: new FillHolder ((owned) xdata, (owned) lower, (owned) upper));
            override (parameters);
        }
    }
}
