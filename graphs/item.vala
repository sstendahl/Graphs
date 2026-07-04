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

    /**
     * Item factory for creating Python items.
     */
    public class ItemFactory : Object {
        private static ItemFactory instance;

        construct {
            instance = this;
        }

        protected signal DataItem data_item_request (StyleParameters parameters, DataHolder holder);
        protected signal GeneratedDataItem generated_data_item_request (StyleParameters parameters, Expression equation, string xstart, string xstop, int steps, Scale scale);
        protected signal EquationItem equation_item_request (StyleParameters parameters, Expression equation);
        protected signal TextItem text_item_request (StyleParameters parameters, double xanchor, double yanchor, string text);
        protected signal FillItem fill_item_request ();

        public static DataItem new_data_item (StyleParameters parameters, owned double[] xdata, owned double[] ydata, owned double[]? xerr = null, owned double[]? yerr = null) {
            return instance.data_item_request.emit (parameters, new DataHolder ((owned) xdata, (owned) ydata, (owned) xerr, (owned) yerr));
        }

        public static GeneratedDataItem new_generated_data_item (StyleParameters parameters, Expression equation, string xstart, string xstop, int steps, Scale scale) {
            return instance.generated_data_item_request.emit (parameters, equation, xstart, xstop, steps, scale);
        }

        public static EquationItem new_equation_item (StyleParameters parameters, Expression equation) {
            return instance.equation_item_request.emit (parameters, equation);
        }

        public static TextItem new_text_item (StyleParameters parameters, double xanchor, double yanchor, string text) {
            return instance.text_item_request.emit (parameters, xanchor, yanchor, text);
        }

        public static FillItem new_fill_item () {
            return instance.fill_item_request.emit ();
        }
    }

    /**
     * Base item class
     */
    public class Item : Object {
        public string typename { get; construct set; }
        public string name { get; set; default = ""; }
        public string color { get; set; default = ""; }
        public float alpha { get; set; default = 1; }
        public bool selected { get; set; default = true; }
        public bool legend { get; set; default = true; }
        public string xlabel { get; set; default = ""; }
        public string ylabel { get; set; default = ""; }
        public XPosition xposition { get; set; default = XPosition.BOTTOM; }
        public YPosition yposition { get; set; default = YPosition.LEFT; }
        public bool fillenabled { get; set; default = false; }
        public FillDirection filldirection { get; set; default = FillDirection.BELOW; }
        public int fillreference { get; set; default = -1; }
        public string fillcolor { get; set; default = ""; }
        public double fillalpha { get; set; default = 0.25; }

        private FillItem? _fill = null;
        public FillItem fill {
            get {
                if (_fill == null) _fill = ItemFactory.new_fill_item ();
                return _fill;
            }
        }

        public Gdk.RGBA get_rgba () {
            Gdk.RGBA rgba = Tools.hex_to_rgba (color);
            rgba.alpha = alpha;
            return rgba;
        }

        public void set_rgba (Gdk.RGBA rgba) {
            this.color = Tools.rgba_to_hex (rgba);
            this.alpha = rgba.alpha;
        }
    }

    public interface EquationBasedItem : Item {
        public abstract Expression equation { get; set; }
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
        public int linestyle { get; set; default = 1; }
        public double linewidth { get; set; default = 3; }
        public int markerstyle { get; set; default = 0; }
        public double markersize { get; set; default = 7; }
        public bool showxerr { get; set; default = true; }
        public bool showyerr { get; set; default = true; }

        construct {
            typename = _("Dataset");
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

        private Expression _equation;
        public Expression equation {
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
        public int linestyle { get; set; default = 1; }
        public double linewidth { get; set; default = 3; }

        private Expression _equation;
        public Expression equation {
            get { return _equation; }
            set {
                try {
                    if (_equation != null && "Y = " + ast_to_expression (_equation) == name)
                        name = "Y = " + ast_to_expression (value);

                    _equation = value;
                } catch (MathError e) { assert_not_reached (); }
            }
        }

        construct {
            typename = _("Equation");
        }
    }

    public class TextItem : Item {
        public double xanchor { get; set; default = 0; }
        public double yanchor { get; set; default = 0; }
        public string text { get; set; default = ""; }
        public double size { get; set; default = 12; }
        public int rotation { get; set; default = 0; }

        construct {
            typename = _("Label");
        }
    }

    public class FillItem : Item {
        construct {
            typename = _("Fill");
        }
    }
}
