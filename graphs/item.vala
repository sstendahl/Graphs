// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * Small list class
     */
    public class ItemList : Object {
        private ManagedArray<Item> _items = new ManagedArray<Item> ();

        public void add (Item item) {
            _items.append (item);
        }

        public void add_all (Item[] items) {
            _items.append_all (items);
        }

        public Item[] to_array () {
            return _items.steal ();
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

        protected signal void reset_request (Item item, StyleParameters old_style, StyleParameters new_style);
        protected signal void override_request (Item item, StyleParameters parameters);

        protected signal DataItem data_item_request (StyleParameters parameters, DataHolder holder);
        protected signal GeneratedDataItem generated_data_item_request (StyleParameters parameters, Ast equation, string xstart, string xstop, int steps, Scale scale);
        protected signal EquationItem equation_item_request (StyleParameters parameters, Ast equation);
        protected signal TextItem text_item_request (StyleParameters parameters, double xanchor, double yanchor, string text);
        protected signal FillItem fill_item_request (StyleParameters parameters, FillHolder holder);

        public static void reset_item (Item item, StyleParameters old_style, StyleParameters new_style) {
            instance.reset_request.emit (item, old_style, new_style);
        }

        public static void override_item (Item item, StyleParameters parameters) {
            instance.override_request.emit (item, parameters);
        }

        public static DataItem new_data_item (StyleParameters parameters, owned double[] xdata, owned double[] ydata, owned double[]? xerr = null, owned double[]? yerr = null) {
            return instance.data_item_request.emit (parameters, new DataHolder ((owned) xdata, (owned) ydata, (owned) xerr, (owned) yerr));
        }

        public static GeneratedDataItem new_generated_data_item (StyleParameters parameters, Ast equation, string xstart, string xstop, int steps, Scale scale) {
            return instance.generated_data_item_request.emit (parameters, equation, xstart, xstop, steps, scale);
        }

        public static EquationItem new_equation_item (StyleParameters parameters, Ast equation) {
            return instance.equation_item_request.emit (parameters, equation);
        }

        public static TextItem new_text_item (StyleParameters parameters, double xanchor, double yanchor, string text) {
            return instance.text_item_request.emit (parameters, xanchor, yanchor, text);
        }

        public static FillItem new_fill_item (StyleParameters parameters, owned double[] xdata, owned double[] lower, owned double[] upper) {
            return instance.fill_item_request.emit (parameters, new FillHolder ((owned) xdata, (owned) lower, (owned) upper));
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
    }

    public interface LegendableItem : Item {
        public abstract bool legend { get; set; }
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

    public class DataItem : Item, LegendableItem {
        public DataHolder data { get; set; default = new DataHolder.empty (); }
        public bool errbarsabove { get; set; default = false; }
        public double errcapsize { get; set; default = 0; }
        public double errcapthick { get; set; default = 1; }
        public string errcolor { get; set; default = ""; }
        public double errlinewidth { get; set; default = 1; }
        public bool legend { get; set; default = true; }
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

    public class EquationItem : Item, EquationBasedItem, LegendableItem {
        public bool legend { get; set; default = true; }
        public int linestyle { get; set; default = 1; }
        public double linewidth { get; set; default = 3; }

        private Ast _equation;
        private Program _program;
        public Ast equation {
            get { return _equation; }
            set {
                try {
                    if (_equation != null && "Y = " + ast_to_expression (_equation) == name)
                        name = "Y = " + ast_to_expression (value);

                    _equation = value;
                    _program = ast_to_program (value);
                } catch (MathError e) { assert_not_reached (); }
            }
        }

        construct {
            typename = _("Equation");
        }

        public unowned Program get_program () {
            return _program;
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

        public Bytes get_xdata_b () {
            return new Bytes ((uint8[]) _xdata);
        }

        public Bytes get_lower_b () {
            return new Bytes ((uint8[]) _lower);
        }

        public Bytes get_upper_b () {
            return new Bytes ((uint8[]) _upper);
        }
    }

    public enum FillBoundKind {
        DATA,
        ITEM,
        EQUATION
    }

    public class FillBounds : Object {
        public const uint INF = 0;
        public const uint NEG_INF = 1;
        public const uint CUSTOM = 2;
        public const uint ITEMS = 3;

        public static Item[] get_source_items (Data data) {
            var items = new Gee.ArrayList<Item> ();
            foreach (Item item in data) {
                if (item is DataItem || item is EquationItem) items.add (item);
            }
            return items.to_array ();
        }

        public static Gtk.StringList create_model (Item[] source_items) {
            var model = new Gtk.StringList (null);
            model.append (_("Positive Infinity"));
            model.append (_("Negative Infinity"));
            model.append (_("Custom Equation…"));
            foreach (Item item in source_items) {
                model.append (item.name);
            }
            return model;
        }

        public static string? get_expression (uint selected) {
            switch (selected) {
                case INF: return "inf";
                case NEG_INF: return "-inf";
                default: return null;
            }
        }

        public static uint get_selection (
            FillBoundKind kind, Item? source, Ast? equation,
            Item[] source_items
        ) {
            if (kind == FillBoundKind.ITEM) {
                if (source != null) {
                    for (uint i = 0; i < source_items.length; i++) {
                        if (source_items[i] == source) return ITEMS + i;
                    }
                }
                return CUSTOM;
            }
            if (equation == null) return CUSTOM;
            string expression;
            try {
                expression = ast_to_expression (equation);
            } catch (MathError e) { return CUSTOM; }
            switch (expression) {
                case "inf": return INF;
                case "-inf": return NEG_INF;
                default: return CUSTOM;
            }
        }
    }

    public class FillItem : Item, LegendableItem {
        public FillHolder data { get; set; default = new FillHolder.empty (); }

        public bool legend { get; set; default = false; }
        public signal void bounds_changed ();

        private FillBoundKind _upper_kind = FillBoundKind.DATA;
        private Item? _upper_item = null;
        private Ast? _upper_equation = null;
        private Program? _upper_program = null;
        private ulong _upper_handler = 0;

        private FillBoundKind _lower_kind = FillBoundKind.DATA;
        private Item? _lower_item = null;
        private Ast? _lower_equation = null;
        private Program? _lower_program = null;
        private ulong _lower_handler = 0;

        private Item? _color_source = null;
        private ulong _color_handler = 0;

        construct {
            typename = _("Fill");
            alpha = 0.4f;
        }

        public FillBoundKind get_upper_kind () {
            return _upper_kind;
        }

        public Item? get_upper_source () {
            return _upper_item;
        }

        public Ast? get_upper_equation () {
            return _upper_equation;
        }

        public unowned Program? get_upper_program () {
            return _upper_program;
        }

        public FillBoundKind get_lower_kind () {
            return _lower_kind;
        }

        public Item? get_lower_source () {
            return _lower_item;
        }

        public Ast? get_lower_equation () {
            return _lower_equation;
        }

        public unowned Program? get_lower_program () {
            return _lower_program;
        }

        public void set_upper_source (Item item) {
            disconnect_source (_upper_item, ref _upper_handler);
            _upper_kind = FillBoundKind.ITEM;
            _upper_item = item;
            _upper_equation = null;
            _upper_program = null;
            _upper_handler = connect_source (item);
            update_color_binding ();
            recompute ();
        }

        public void set_upper_equation (Ast equation) {
            disconnect_source (_upper_item, ref _upper_handler);
            _upper_kind = FillBoundKind.EQUATION;
            _upper_item = null;
            _upper_equation = equation;
            try {
                _upper_program = ast_to_program (equation, "x", false);
            } catch (MathError e) { assert_not_reached (); }
            update_color_binding ();
            recompute ();
        }

        public void set_lower_source (Item item) {
            disconnect_source (_lower_item, ref _lower_handler);
            _lower_kind = FillBoundKind.ITEM;
            _lower_item = item;
            _lower_equation = null;
            _lower_program = null;
            _lower_handler = connect_source (item);
            update_color_binding ();
            recompute ();
        }

        public void set_lower_equation (Ast equation) {
            disconnect_source (_lower_item, ref _lower_handler);
            _lower_kind = FillBoundKind.EQUATION;
            _lower_item = null;
            _lower_equation = equation;
            try {
                _lower_program = ast_to_program (equation, "x", false);
            } catch (MathError e) { assert_not_reached (); }
            update_color_binding ();
            recompute ();
        }

        private ulong connect_source (Item item) {
            if (item is DataItem) {
                return item.notify["data"].connect ((s, p) => recompute ());
            } else if (item is EquationItem) {
                return item.notify["equation"].connect ((s, p) => recompute ());
            }
            return 0;
        }

        private void disconnect_source (Item? source, ref ulong handler) {
            if (source != null && handler != 0) source.disconnect (handler);
            handler = 0;
        }

        private void update_color_binding () {
            Item? driver = null;
            if (_upper_kind == FillBoundKind.ITEM) {
                driver = _upper_item;
            } else if (_lower_kind == FillBoundKind.ITEM) {
                driver = _lower_item;
            }
            if (driver == _color_source) return;
            if (_color_source != null && _color_handler != 0) {
                _color_source.disconnect (_color_handler);
                _color_handler = 0;
            }
            _color_source = driver;
            if (driver == null) return;

            this.color = driver.color;
            _color_handler = driver.notify["color"].connect ((s, p) => {
                this.color = ((Item) s).color;
            });
        }

        public override void dispose () {
            disconnect_source (_upper_item, ref _upper_handler);
            disconnect_source (_lower_item, ref _lower_handler);
            if (_color_source != null && _color_handler != 0) {
                _color_source.disconnect (_color_handler);
                _color_handler = 0;
            }
            base.dispose ();
        }

        private unowned double[]? get_target_x () {
            if (_upper_kind == FillBoundKind.ITEM && _upper_item is DataItem) {
                return ((DataItem) _upper_item).get_xdata ();
            }
            if (_lower_kind == FillBoundKind.ITEM && _lower_item is DataItem) {
                return ((DataItem) _lower_item).get_xdata ();
            }
            return null;
        }

        private double[] evaluate_bound (
            FillBoundKind kind, Item? item, Program? program, double[] target
        ) throws MathError {
            if (kind != FillBoundKind.ITEM) {
                if (program == null) return new double[target.length];
                return program.eval (target);
            }
            if (item is DataItem) {
                var source = (DataItem) item;
                return MathTools.interpolate (
                    source.get_xdata (), source.get_ydata (), target
                );
            }
            return ((EquationItem) item).get_program ().eval (target);
        }

        public bool is_view_based () {
            return get_target_x () == null;
        }

        public void evaluate_bounds (
            double[] xdata, out double[] lower, out double[] upper
        ) throws MathError {
            lower = evaluate_bound (
                _lower_kind, _lower_item, _lower_program, xdata
            );
            upper = evaluate_bound (
                _upper_kind, _upper_item, _upper_program, xdata
            );
        }

        private void recompute () {
            unowned double[]? target = get_target_x ();
            if (target != null) {
                double[] x = new double[target.length];
                for (int i = 0; i < target.length; i++) x[i] = target[i];

                try {
                    double[] lower, upper;
                    evaluate_bounds (x, out lower, out upper);
                    data = new FillHolder (
                        (owned) x, (owned) lower, (owned) upper
                    );
                } catch (MathError e) {
                    warning ("Failed to evaluate fill bounds: %s", e.message);
                }
            }
            bounds_changed ();
        }
    }
}
