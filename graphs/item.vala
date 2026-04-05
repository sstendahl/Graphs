// SPDX-License-Identifier: GPL-3.0-or-later
using Gdk;

namespace Graphs {
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
        public int xposition { get; set; default = 0; }
        public int yposition { get; set; default = 0; }

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
        public abstract string equation { get; set; }
    }

    public class DataItem : Item {
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
    }

    public class GeneratedDataItem : DataItem, EquationBasedItem {
        public string xstart { get; set; default = "0"; }
        public string xstop { get; set; default = "10"; }
        public int steps { get; set; default = 100; }
        public Scale scale { get; set; default = Scale.LINEAR; }

        private string _equation = "";
        public string equation {
            get { return _equation; }
            set {
                string old_equation = _equation;
                if (old_equation == value) return;

                _equation = value;

                if ("Y =" + old_equation == name)
                    name = "Y = " + value;
            }
        }

        construct {
            typename = _("Generated Dataset");
        }
    }

    public class EquationItem : Item, EquationBasedItem {
        public int linestyle { get; set; default = 1; }
        public double linewidth { get; set; default = 3; }

        private string _equation = "";
        private string _preprocessed_equation = "";
        public string equation {
            get { return _equation; }
            set {
                string old_equation = _equation;
                if (old_equation == value) return;

                _equation = value;
                try {
                    _preprocessed_equation = preprocess_equation (value);
                } catch (MathError e) { assert_not_reached (); }

                if ("Y =" + old_equation == name)
                    name = "Y = " + value;
            }
        }

        construct {
            typename = _("Equation");
        }

        public string get_preprocessed_equation () {
            return _preprocessed_equation;
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
