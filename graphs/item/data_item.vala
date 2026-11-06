// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
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

        public Bytes get_xdata_b () {
            return new Bytes ((uint8[]) _xdata);
        }

        public Bytes get_ydata_b () {
            return new Bytes ((uint8[]) _ydata);
        }

        public Bytes? get_xerr_b () {
            return _xerr == null ? null : new Bytes ((uint8[]) _xerr);
        }

        public Bytes? get_yerr_b () {
            return _yerr == null ? null : new Bytes ((uint8[]) _yerr);
        }
    }

    public enum DataLinestyle {
        NONE,
        SOLID,
        DOTTED,
        DASHED,
        DASHDOT;

        public unowned string to_style () {
            EnumClass enumc = (EnumClass) typeof (DataLinestyle).class_ref ();
            unowned EnumValue? eval = enumc.get_value (this);
            return eval.value_nick;
        }

        public static DataLinestyle from_style (string style) {
            EnumClass enumc = (EnumClass) typeof (DataLinestyle).class_ref ();
            unowned EnumValue? eval = enumc.get_value_by_nick (style);
            return (DataLinestyle) eval.value;
        }
    }

    public enum DataMarkerstyle {
        NONE,
        POINT,
        PIXEL,
        CIRCLE,
        TRIANGLE_DOWN,
        TRIANGLE_UP,
        TRIANGLE_LEFT,
        TRIANGLE_RIGHT,
        OCTAGON,
        SQUARE,
        PENTAGON,
        STAR,
        HEXAGON_1,
        HEXAGON_2,
        PLUS,
        X,
        DIAMOND,
        THIN_DIAMOND,
        VERTCAL_LINE,
        HORIZONTAL_LINE,
        FILLED_PLUS,
        FILLED_X;

        private const string[] STYLE_VALUES = {"none", ".", ",", "o", "v", "^", "<", ">", "8", "s", "p", "*", "h", "H", "+", "x", "D", "d", "|", "_", "P", "X"};

        public unowned string to_style () {
            return STYLE_VALUES[this];
        }

        public static DataMarkerstyle from_style (string style) {
            for (int i = 0; i < STYLE_VALUES.length; i++) {
                if (STYLE_VALUES[i] == style) return i;
            }
            assert_not_reached ();
        }
    }

    public class DataItem : Item, LegendableItem {
        public DataHolder data { get; set; default = new DataHolder.empty (); }
        public bool downsample { get; set; default = true; }
        public bool errbarsabove { get; set; default = false; }
        public double errcapsize { get; set; default = 0; }
        public double errcapthick { get; set; default = 1; }
        public string errcolor { get; set; default = ""; }
        public double errlinewidth { get; set; default = 1; }
        public bool legend { get; set; default = true; }
        public DataLinestyle linestyle { get; set; default = 1; }
        public double linewidth { get; set; default = 3; }
        public DataMarkerstyle markerstyle { get; set; default = 0; }
        public double markersize { get; set; default = 7; }
        public bool showxerr { get; set; default = true; }
        public bool showyerr { get; set; default = true; }

        construct {
            typename = _("Dataset");
        }

        private static StylePropertyBinding[] bindings = {
            {"linestyle", (s) => s.linestyle},
            {"linewidth", (s) => s.linewidth},
            {"markerstyle", (s) => s.markerstyle},
            {"markersize", (s) => s.markersize},
            {"errbarsabove", (s) => s.errorbar_barsabove},
            {"errcapsize", (s) => s.errorbar_capsize},
            {"errcapthick", (s) => s.errorbar_capthick},
            {"errlinewidth", (s) => s.errorbar_linewidth}
        };

        protected override unowned StylePropertyBinding[]? get_property_bindings () {
            return bindings;
        }

        public unowned double[] get_xdata () {
            return data.get_xdata ();
        }

        public unowned double[] get_ydata () {
            return data.get_ydata ();
        }

        public bool exceeds_downsample_threshold () {
            return get_xdata ().length >= DOWNSAMPLE_THRESHOLD;
        }

        public bool has_xerr () {
            return data.get_xerr () != null;
        }

        public bool has_yerr () {
            return data.get_yerr () != null;
        }
    }
}
