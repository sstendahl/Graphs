// SPDX-License-Identifier: GPL-3.0-or-later
using Gdk;

namespace Graphs {
    /**
     * Base item class
     */
    public class Item : Object {
        public string typename { get; set; default = ""; }
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
    }

    public class GeneratedDataItem : DataItem {
        public string xstart { get; set; default = "0"; }
        public string xstop { get; set; default = "10"; }
        public int steps { get; set; default = 100; }
        public int scale { get; set; default = 0; }
    }

    public class EquationItem : Item {
        public int linestyle { get; set; default = 1; }
        public double linewidth { get; set; default = 3; }
    }

    public class TextItem : Item {
        public double xanchor { get; set; default = 0; }
        public double yanchor { get; set; default = 0; }
        public string text { get; set; default = ""; }
        public double size { get; set; default = 12; }
        public int rotation { get; set; default = 0; }
    }

    public class FillItem : Item {
    }
}
