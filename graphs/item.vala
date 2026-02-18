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
        public bool has_xerr { get; set; default = false; }
        public bool has_yerr { get; set; default = false; }

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
}
